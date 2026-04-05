"""
Load Balancer
-------------
Implements round-robin load balancing for distributing file chunks
across storage nodes. Skips unhealthy nodes to ensure reliability.

Algorithm: Round-Robin
    - Maintains a counter that cycles through available nodes
    - Each new chunk goes to the next node in sequence
    - Ensures even distribution of data across the cluster
"""

import threading
from config import STORAGE_NODES
from logger_config import setup_logger

logger = setup_logger("load_balancer")


class RoundRobinBalancer:
    """
    Round-robin load balancer for distributing chunks to storage nodes.

    How it works:
        1. Maintains a rotating index (_current_index)
        2. On each call to get_next_node(), returns the next node in sequence
        3. Skips over any nodes marked as unhealthy
        4. Thread-safe using a lock for concurrent access
    """

    def __init__(self):
        self._current_index = 0
        self._lock = threading.Lock()  # Thread safety for concurrent uploads

    def get_next_node(self, healthy_nodes):
        """
        Get the next storage node for chunk placement.

        Args:
            healthy_nodes: List of currently healthy node dictionaries

        Returns:
            Node dict {"node_id": ..., "host": ..., "port": ...} or None
        """
        if not healthy_nodes:
            logger.error("No healthy nodes available for chunk placement!")
            return None

        with self._lock:
            # Wrap around if index exceeds list length
            self._current_index = self._current_index % len(healthy_nodes)
            selected_node = healthy_nodes[self._current_index]
            self._current_index += 1

        logger.info(f"Load balancer selected: {selected_node['node_id']} (port {selected_node['port']})")
        return selected_node

    def get_replica_nodes(self, primary_node, healthy_nodes, replication_factor):
        """
        Get additional nodes for chunk replication (excluding the primary node).

        Args:
            primary_node: The node where the primary chunk is stored
            healthy_nodes: All currently healthy nodes
            replication_factor: Total number of copies needed (including primary)

        Returns:
            List of nodes to replicate the chunk to
        """
        # Filter out the primary node
        candidates = [n for n in healthy_nodes if n["node_id"] != primary_node["node_id"]]

        # Select up to (replication_factor - 1) replica nodes
        replicas_needed = min(replication_factor - 1, len(candidates))
        replica_nodes = candidates[:replicas_needed]

        if replica_nodes:
            node_ids = [n["node_id"] for n in replica_nodes]
            logger.info(f"Replica nodes selected: {node_ids}")

        return replica_nodes


# Global load balancer instance (singleton)
load_balancer = RoundRobinBalancer()
