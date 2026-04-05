"""
Metadata Manager
-----------------
Handles all SQLite database operations for managing:
  - Users (authentication)
  - Files (uploaded file records)
  - Chunks (individual chunk records)
  - Chunk Locations (which chunks are on which nodes)

Database Schema:
    users          → id, username, password_hash, created_at
    files          → id, filename, original_name, file_size, chunk_count, owner, created_at
    chunks         → id, chunk_id, file_id, chunk_index, chunk_size
    chunk_locations → id, chunk_id, node_id, is_primary
"""

import sqlite3
import os
from datetime import datetime
from config import DATABASE_PATH
from logger_config import setup_logger

logger = setup_logger("metadata")


def get_db():
    """Create a new database connection (thread-safe)."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
    return conn


def init_database():
    """
    Initialize the database schema.
    Creates all required tables if they don't exist.
    Called once at application startup.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Users table — stores login credentials
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Files table — stores file metadata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT UNIQUE NOT NULL,
            original_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            chunk_count INTEGER NOT NULL,
            owner TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Chunks table — stores individual chunk information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_id TEXT UNIQUE NOT NULL,
            file_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_size INTEGER NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(file_id)
        )
    """)

    # Chunk Locations table — maps chunks to storage nodes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunk_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_id TEXT NOT NULL,
            node_id TEXT NOT NULL,
            is_primary INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id),
            UNIQUE(chunk_id, node_id)
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


# ──────────────────────────────────────────────
# User Operations
# ──────────────────────────────────────────────

def create_user(username, password_hash):
    """
    Register a new user.

    Args:
        username: The username
        password_hash: Bcrypt-hashed password

    Returns:
        True if user was created, False if username already exists
    """
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        conn.close()
        logger.info(f"User created: {username}")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"Username already exists: {username}")
        return False


def get_user(username):
    """
    Retrieve a user by username.

    Returns:
        User row dict or None if not found
    """
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


# ──────────────────────────────────────────────
# File Operations
# ──────────────────────────────────────────────

def save_file_metadata(file_id, original_name, file_size, chunk_count, owner):
    """
    Save metadata for an uploaded file.

    Args:
        file_id: Unique file identifier (UUID)
        original_name: Original file name
        file_size: Total file size in bytes
        chunk_count: Number of chunks the file was split into
        owner: Username of the file owner
    """
    conn = get_db()
    conn.execute(
        """INSERT INTO files (file_id, original_name, file_size, chunk_count, owner)
           VALUES (?, ?, ?, ?, ?)""",
        (file_id, original_name, file_size, chunk_count, owner)
    )
    conn.commit()
    conn.close()
    logger.info(f"File metadata saved: {original_name} (ID: {file_id}, chunks: {chunk_count})")


def get_file_metadata(file_id):
    """Retrieve metadata for a specific file."""
    conn = get_db()
    file_data = conn.execute(
        "SELECT * FROM files WHERE file_id = ?", (file_id,)
    ).fetchone()
    conn.close()
    return dict(file_data) if file_data else None


def get_user_files(username):
    """Retrieve all files belonging to a specific user."""
    conn = get_db()
    files = conn.execute(
        "SELECT * FROM files WHERE owner = ? ORDER BY created_at DESC", (username,)
    ).fetchall()
    conn.close()
    return [dict(f) for f in files]


def delete_file_metadata(file_id):
    """
    Delete all metadata for a file (file record, chunks, chunk locations).

    Args:
        file_id: The file ID to delete

    Returns:
        List of chunk_ids that were deleted (used to remove from storage nodes)
    """
    conn = get_db()

    # Get all chunks for this file
    chunks = conn.execute(
        "SELECT chunk_id FROM chunks WHERE file_id = ?", (file_id,)
    ).fetchall()
    chunk_ids = [c["chunk_id"] for c in chunks]

    # Delete chunk locations
    for chunk_id in chunk_ids:
        conn.execute("DELETE FROM chunk_locations WHERE chunk_id = ?", (chunk_id,))

    # Delete chunks
    conn.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))

    # Delete file record
    conn.execute("DELETE FROM files WHERE file_id = ?", (file_id,))

    conn.commit()
    conn.close()
    logger.info(f"Deleted all metadata for file: {file_id}")
    return chunk_ids


# ──────────────────────────────────────────────
# Chunk Operations
# ──────────────────────────────────────────────

def save_chunk_metadata(chunk_id, file_id, chunk_index, chunk_size):
    """Save metadata for an individual chunk."""
    conn = get_db()
    conn.execute(
        """INSERT INTO chunks (chunk_id, file_id, chunk_index, chunk_size)
           VALUES (?, ?, ?, ?)""",
        (chunk_id, file_id, chunk_index, chunk_size)
    )
    conn.commit()
    conn.close()


def save_chunk_location(chunk_id, node_id, is_primary=False):
    """Record that a chunk is stored on a specific node."""
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO chunk_locations (chunk_id, node_id, is_primary)
               VALUES (?, ?, ?)""",
            (chunk_id, node_id, 1 if is_primary else 0)
        )
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        # Chunk already exists on this node (duplicate insert)
        pass


def get_chunk_locations(chunk_id):
    """Get all node locations where a specific chunk is stored."""
    conn = get_db()
    locations = conn.execute(
        "SELECT node_id, is_primary FROM chunk_locations WHERE chunk_id = ?",
        (chunk_id,)
    ).fetchall()
    conn.close()
    return [dict(loc) for loc in locations]


def get_file_chunks(file_id):
    """Get all chunks for a file, ordered by chunk index."""
    conn = get_db()
    chunks = conn.execute(
        "SELECT * FROM chunks WHERE file_id = ? ORDER BY chunk_index", (file_id,)
    ).fetchall()
    conn.close()
    return [dict(c) for c in chunks]
