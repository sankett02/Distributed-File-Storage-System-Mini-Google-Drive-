"""
Health Monitor
--------------
Background thread that periodically pings all storage nodes
to check their health status. Maintains a global registry of
which nodes are alive and which are down.

Features:
    - Background health checking every N seconds
    - Tracks node status with timestamps
    - Provides API endpoints for node health info
    - Supports manual node toggling (simulate failure)
"""

import threading
import time
import requests
from datetime import datetime
from flask import Blueprint, jsonify, request
from config import STORAGE_NODES, HEALTH_CHECK_INTERVAL, HEALTH_CHECK_TIMEOUT
from logger_config import setup_logger

# Create Flask Blueprint for health routes
health_bp = Blueprint("health", __name__)
logger = setup_logger("health_monitor")

# ──────────────────────────────────────────────
# Global Node Status Registry
# ──────────────────────────────────────────────

# Stores the current status of each node
# Format: { "node1": {"status": "healthy", "last_check": "2024-...", ...}, ... }
node_status = {}

# Set of manually disabled nodes (simulating failure)
disabled_nodes = set()

# Lock for thread-safe access to node_status
_status_lock = threading.RLock()


def init_node_status():
    """Initialize the status registry for all configured nodes."""
    with _status_lock:
        for node in STORAGE_NODES:
            node_status[node["node_id"]] = {
                "node_id": node["node_id"],
                "host": node["host"],
                "port": node["port"],
                "status": "unknown",
                "last_check": None,
                "chunk_count": 0,
                "disk_usage_mb": 0,
            }
    logger.info(f"Initialized status tracking for {len(STORAGE_NODES)} nodes")


# ──────────────────────────────────────────────
# Health Check Logic
# ──────────────────────────────────────────────

def check_node_health(node):
    """
    Ping a single storage node to check if it's alive.

    Args:
        node: Node dict with host and port

    Returns:
        True if node is healthy, False otherwise
    """
    # If node is manually disabled (simulating failure), mark as dead
    if node["node_id"] in disabled_nodes:
        return False

    try:
        url = f"http://{node['host']}:{node['port']}/health"
        response = requests.get(url, timeout=HEALTH_CHECK_TIMEOUT)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def update_node_status(node, is_healthy):
    """
    Update the global status registry for a node.

    Args:
        node: Node dict
        is_healthy: Boolean indicating health
    """
    with _status_lock:
        prev_status = node_status.get(node["node_id"], {}).get("status")
        new_status = "healthy" if is_healthy else "dead"

        node_status[node["node_id"]]["status"] = new_status
        node_status[node["node_id"]]["last_check"] = datetime.now().isoformat()

        # Try to get detailed status if node is healthy
        if is_healthy and node["node_id"] not in disabled_nodes:
            try:
                url = f"http://{node['host']}:{node['port']}/status"
                response = requests.get(url, timeout=HEALTH_CHECK_TIMEOUT)
                if response.status_code == 200:
                    status_data = response.json()
                    node_status[node["node_id"]]["chunk_count"] = status_data.get("chunk_count", 0)
                    node_status[node["node_id"]]["disk_usage_mb"] = status_data.get("disk_usage_mb", 0)
            except:
                pass

        # Log status changes
        if prev_status != new_status:
            if new_status == "dead":
                logger.warning(f"Node {node['node_id']} is DOWN!")
            else:
                logger.info(f"Node {node['node_id']} is back UP")


def run_health_checks():
    """Run a single round of health checks on all nodes."""
    for node in STORAGE_NODES:
        is_healthy = check_node_health(node)
        update_node_status(node, is_healthy)


def health_check_loop():
    """
    Background loop that continuously monitors node health.
    Runs in a daemon thread — stops when the main app stops.
    """
    logger.info(f"Health monitor started (interval: {HEALTH_CHECK_INTERVAL}s)")
    while True:
        run_health_checks()
        time.sleep(HEALTH_CHECK_INTERVAL)


def start_health_monitor():
    """Start the background health check thread."""
    init_node_status()
    monitor_thread = threading.Thread(target=health_check_loop, daemon=True)
    monitor_thread.start()
    logger.info("Background health monitor thread started")


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def get_healthy_nodes():
    """
    Get a list of all currently healthy nodes.

    Returns:
        List of node dicts from STORAGE_NODES that are healthy
    """
    with _status_lock:
        healthy = []
        for node in STORAGE_NODES:
            if (node_status.get(node["node_id"], {}).get("status") == "healthy"
                    and node["node_id"] not in disabled_nodes):
                healthy.append(node)
        return healthy


def is_node_healthy(node_id):
    """Check if a specific node is currently healthy."""
    with _status_lock:
        return (node_status.get(node_id, {}).get("status") == "healthy"
                and node_id not in disabled_nodes)


# ──────────────────────────────────────────────
# API Endpoints
# ──────────────────────────────────────────────

@health_bp.route("/api/nodes", methods=["GET"])
def get_all_node_status():
    """Return the health status of all storage nodes."""
    with _status_lock:
        # We can call get_healthy_nodes because we use RLock
        healthy_nodes = get_healthy_nodes()
        return jsonify({
            "nodes": list(node_status.values()),
            "healthy_count": len(healthy_nodes),
            "total_count": len(STORAGE_NODES)
        }), 200


@health_bp.route("/api/nodes/<node_id>/toggle", methods=["POST"])
def toggle_node(node_id):
    """
    Toggle a node on/off to simulate failure.
    Used for demonstrating fault tolerance.
    """
    if node_id in disabled_nodes:
        # Re-enable the node
        disabled_nodes.discard(node_id)
        logger.info(f"Node {node_id} manually RE-ENABLED")
        # Immediately run health check for this node
        for node in STORAGE_NODES:
            if node["node_id"] == node_id:
                is_healthy = check_node_health(node)
                update_node_status(node, is_healthy)
                break
        return jsonify({"message": f"Node {node_id} enabled", "status": "healthy"}), 200
    else:
        # Disable the node (simulate failure)
        disabled_nodes.add(node_id)
        # Update status immediately
        with _status_lock:
            node_status[node_id]["status"] = "dead"
            node_status[node_id]["last_check"] = datetime.now().isoformat()
        logger.warning(f"Node {node_id} manually DISABLED (simulating failure)")
        return jsonify({"message": f"Node {node_id} disabled", "status": "dead"}), 200
