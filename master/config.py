"""
Master Node Configuration
-------------------------
Central configuration for the master/coordinator node.
All constants and settings are defined here for easy modification.
"""

import os

# ──────────────────────────────────────────────
# Server Settings
# ──────────────────────────────────────────────

MASTER_HOST = "0.0.0.0"
MASTER_PORT = 5000

# Secret key for Flask sessions (change in production)
SECRET_KEY = "distributed-file-storage-secret-key-2024"

# ──────────────────────────────────────────────
# Storage Node Configuration
# ──────────────────────────────────────────────

# List of storage nodes in the cluster
STORAGE_NODES = [
    {"node_id": "node1", "host": "localhost", "port": 5001},
    {"node_id": "node2", "host": "localhost", "port": 5002},
    {"node_id": "node3", "host": "localhost", "port": 5003},
]

# ──────────────────────────────────────────────
# File Chunking Settings
# ──────────────────────────────────────────────

# Size of each chunk in bytes (256 KB)
CHUNK_SIZE = 256 * 1024  # 262144 bytes

# Maximum file upload size (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# ──────────────────────────────────────────────
# Replication Settings
# ──────────────────────────────────────────────

# Number of copies for each chunk (including the primary)
# With 3 nodes and REPLICATION_FACTOR=2, each chunk is on 2 nodes
REPLICATION_FACTOR = 2

# ──────────────────────────────────────────────
# Health Monitor Settings
# ──────────────────────────────────────────────

# How often to check node health (in seconds)
HEALTH_CHECK_INTERVAL = 10

# Timeout for health check HTTP requests (in seconds)
HEALTH_CHECK_TIMEOUT = 3

# ──────────────────────────────────────────────
# Database Settings
# ──────────────────────────────────────────────

# SQLite database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

# ──────────────────────────────────────────────
# Logging Settings
# ──────────────────────────────────────────────

LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "master.log")
os.makedirs(LOG_DIR, exist_ok=True)
