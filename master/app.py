"""
Master Node — Main Application
-------------------------------
The central coordinator of the Distributed File Storage System.

Responsibilities:
    - Serve the frontend UI (static files)
    - Handle user authentication (auth blueprint)
    - Manage file operations (file_manager blueprint)
    - Monitor storage node health (health_monitor blueprint)
    - Initialize the metadata database on startup

This is the entry point — run this file to start the master node.
Usage: python app.py
"""

import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import MASTER_HOST, MASTER_PORT, SECRET_KEY, MAX_FILE_SIZE
from metadata import init_database
from auth import auth_bp
from file_manager import file_bp
from health_monitor import health_bp, start_health_monitor
from logger_config import setup_logger

# ──────────────────────────────────────────────
# Initialize Flask Application
# ──────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE  # Limit upload size

# Enable CORS (Cross-Origin Resource Sharing) for frontend
CORS(app, supports_credentials=True)

# Setup logging
logger = setup_logger("master")

# ──────────────────────────────────────────────
# Register Blueprints (modular routes)
# ──────────────────────────────────────────────

app.register_blueprint(auth_bp)       # /api/signup, /api/login, etc.
app.register_blueprint(file_bp)       # /api/upload, /api/download, etc.
app.register_blueprint(health_bp)     # /api/nodes, /api/nodes/<id>/toggle

# ──────────────────────────────────────────────
# Serve Frontend Static Files
# ──────────────────────────────────────────────

# Path to the frontend directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")


@app.route("/")
def serve_index():
    """Serve the login/signup page."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/dashboard")
def serve_dashboard():
    """Serve the main dashboard page."""
    return send_from_directory(FRONTEND_DIR, "dashboard.html")


@app.route("/css/<path:filename>")
def serve_css(filename):
    """Serve CSS files."""
    return send_from_directory(os.path.join(FRONTEND_DIR, "css"), filename)


@app.route("/js/<path:filename>")
def serve_js(filename):
    """Serve JavaScript files."""
    return send_from_directory(os.path.join(FRONTEND_DIR, "js"), filename)


# ──────────────────────────────────────────────
# Application Startup
# ──────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("  DISTRIBUTED FILE STORAGE SYSTEM — MASTER NODE")
    logger.info("=" * 60)

    # Step 1: Initialize the SQLite database
    init_database()
    logger.info("Database initialized")

    # Step 2: Start the background health monitor
    start_health_monitor()
    logger.info("Health monitor started")

    # Step 3: Start the Flask server
    logger.info(f"Master node starting on http://{MASTER_HOST}:{MASTER_PORT}")
    logger.info(f"Frontend available at http://localhost:{MASTER_PORT}")
    logger.info("=" * 60)

    app.run(host=MASTER_HOST, port=MASTER_PORT, debug=False)
