"""
Storage Node Configuration
--------------------------
Each storage node uses its own storage directory based on node ID.
"""

import os
import argparse


def get_args():
    """Parse command-line arguments for the storage node."""
    parser = argparse.ArgumentParser(description="Distributed Storage Node")
    parser.add_argument("--port", type=int, default=5001, help="Port to run the storage node on")
    parser.add_argument("--node-id", type=str, default="node1", help="Unique identifier for this node")
    return parser.parse_args()


# Default configuration (overridden at runtime via CLI args)
DEFAULT_PORT = 5001
DEFAULT_NODE_ID = "node1"

# Maximum storage per node (in bytes) — 2 GB limit for demo
MAX_STORAGE_BYTES = 2 * 1024 * 1024 * 1024


def get_storage_dir(node_id):
    """Return the storage directory path for a given node."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    storage_dir = os.path.join(base_dir, "storage", node_id)
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir
