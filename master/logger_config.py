"""
Logger Configuration
--------------------
Sets up structured logging for the master node.
Logs are written to both console and a log file.
"""

import logging
import os
from config import LOG_FILE, LOG_DIR


def setup_logger(name="master"):
    """
    Create and configure a logger instance.

    Args:
        name: Logger name (default: 'master')

    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Log format: [MASTER] 2024-01-01 12:00:00 - INFO - Message
    formatter = logging.Formatter(
        f"[{name.upper()}] %(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler — shows logs in terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler — saves logs to file
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
