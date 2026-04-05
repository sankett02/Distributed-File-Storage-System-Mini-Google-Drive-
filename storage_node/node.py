"""
Storage Node Server
-------------------
A lightweight Flask server that stores, retrieves, and deletes file chunks.
Each storage node runs independently on its own port.

Endpoints:
    POST   /store_chunk       — Store a file chunk
    GET    /get_chunk/<id>     — Retrieve a file chunk
    DELETE /delete_chunk/<id>  — Delete a file chunk
    GET    /health             — Health check (returns 200 if alive)
    GET    /status             — Node statistics (chunk count, disk usage)
"""

import os
import logging
from flask import Flask, request, jsonify, send_file
from config import get_args, get_storage_dir, MAX_STORAGE_BYTES

# ──────────────────────────────────────────────
# Initialize Flask App
# ──────────────────────────────────────────────

app = Flask(__name__)
args = get_args()
NODE_ID = args.node_id
PORT = args.port
STORAGE_DIR = get_storage_dir(NODE_ID)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format=f"[{NODE_ID}] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def get_chunk_path(chunk_id):
    """Get the full file path for a given chunk ID."""
    return os.path.join(STORAGE_DIR, chunk_id)


def get_disk_usage():
    """Calculate total disk usage of this node's storage directory."""
    total_size = 0
    for filename in os.listdir(STORAGE_DIR):
        filepath = os.path.join(STORAGE_DIR, filename)
        if os.path.isfile(filepath):
            total_size += os.path.getsize(filepath)
    return total_size


# ──────────────────────────────────────────────
# API Endpoints
# ──────────────────────────────────────────────

@app.route("/store_chunk", methods=["POST"])
def store_chunk():
    """
    Store a file chunk on this node.
    Expects: multipart form data with 'chunk' file and 'chunk_id' field.
    """
    try:
        chunk_id = request.form.get("chunk_id")
        chunk_file = request.files.get("chunk")

        # Validate input
        if not chunk_id or not chunk_file:
            return jsonify({"error": "Missing chunk_id or chunk data"}), 400

        # Check storage capacity
        current_usage = get_disk_usage()
        if current_usage >= MAX_STORAGE_BYTES:
            logger.warning(f"Storage full! Cannot store chunk {chunk_id}")
            return jsonify({"error": "Node storage is full"}), 507

        # Save chunk to disk
        chunk_path = get_chunk_path(chunk_id)
        chunk_file.save(chunk_path)

        logger.info(f"Stored chunk: {chunk_id} ({os.path.getsize(chunk_path)} bytes)")
        return jsonify({
            "status": "success",
            "node_id": NODE_ID,
            "chunk_id": chunk_id,
            "size": os.path.getsize(chunk_path)
        }), 200

    except Exception as e:
        logger.error(f"Error storing chunk {chunk_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_chunk/<chunk_id>", methods=["GET"])
def get_chunk(chunk_id):
    """
    Retrieve a stored chunk by its ID.
    Returns the raw file data as a binary response.
    """
    try:
        chunk_path = get_chunk_path(chunk_id)

        if not os.path.exists(chunk_path):
            logger.warning(f"Chunk not found: {chunk_id}")
            return jsonify({"error": "Chunk not found"}), 404

        logger.info(f"Serving chunk: {chunk_id}")
        return send_file(chunk_path, mimetype="application/octet-stream")

    except Exception as e:
        logger.error(f"Error retrieving chunk {chunk_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/delete_chunk/<chunk_id>", methods=["DELETE"])
def delete_chunk(chunk_id):
    """
    Delete a stored chunk by its ID.
    """
    try:
        chunk_path = get_chunk_path(chunk_id)

        if not os.path.exists(chunk_path):
            logger.warning(f"Chunk not found for deletion: {chunk_id}")
            return jsonify({"error": "Chunk not found"}), 404

        # Remove chunk from disk
        file_size = os.path.getsize(chunk_path)
        os.remove(chunk_path)

        logger.info(f"Deleted chunk: {chunk_id} (freed {file_size} bytes)")
        return jsonify({
            "status": "success",
            "node_id": NODE_ID,
            "chunk_id": chunk_id
        }), 200

    except Exception as e:
        logger.error(f"Error deleting chunk {chunk_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    Returns 200 if the node is alive and operational.
    Used by the master node's health monitor.
    """
    return jsonify({
        "status": "healthy",
        "node_id": NODE_ID,
        "port": PORT
    }), 200


@app.route("/status", methods=["GET"])
def node_status():
    """
    Return detailed status of this storage node.
    Includes: chunk count, disk usage, capacity.
    """
    try:
        chunks = [f for f in os.listdir(STORAGE_DIR) if os.path.isfile(os.path.join(STORAGE_DIR, f))]
        disk_usage = get_disk_usage()

        return jsonify({
            "node_id": NODE_ID,
            "port": PORT,
            "status": "healthy",
            "chunk_count": len(chunks),
            "disk_usage_bytes": disk_usage,
            "disk_usage_mb": round(disk_usage / (1024 * 1024), 2),
            "max_storage_mb": round(MAX_STORAGE_BYTES / (1024 * 1024), 2),
            "usage_percent": round((disk_usage / MAX_STORAGE_BYTES) * 100, 2)
        }), 200

    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Start Server
# ──────────────────────────────────────────────

if __name__ == "__main__":
    logger.info(f"Starting Storage Node '{NODE_ID}' on port {PORT}")
    logger.info(f"Storage directory: {STORAGE_DIR}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
