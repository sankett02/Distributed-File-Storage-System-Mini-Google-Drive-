"""
Authentication Module
---------------------
Handles user signup, login, and logout using Flask sessions.
Passwords are hashed using bcrypt for security.

Endpoints:
    POST /api/signup  — Register a new user
    POST /api/login   — Authenticate and create session
    POST /api/logout  — Destroy session
    GET  /api/me      — Get current logged-in user
"""

from flask import Blueprint, request, jsonify, session
import bcrypt
from metadata import create_user, get_user
from logger_config import setup_logger

# Create Flask Blueprint for auth routes
auth_bp = Blueprint("auth", __name__)
logger = setup_logger("auth")


def login_required(f):
    """
    Decorator to protect routes that require authentication.
    Returns 401 if user is not logged in.
    """
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "Authentication required. Please login."}), 401
        return f(*args, **kwargs)

    return decorated_function


@auth_bp.route("/api/signup", methods=["POST"])
def signup():
    """
    Register a new user.
    Expects JSON: {"username": "...", "password": "..."}
    """
    data = request.get_json()

    # Validate input
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400

    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters"}), 400

    # Hash the password using bcrypt
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    # Try to create the user
    if create_user(username, password_hash):
        logger.info(f"New user registered: {username}")
        return jsonify({"message": "User registered successfully"}), 201
    else:
        return jsonify({"error": "Username already exists"}), 409


@auth_bp.route("/api/login", methods=["POST"])
def login():
    """
    Authenticate a user and create a session.
    Expects JSON: {"username": "...", "password": "..."}
    """
    data = request.get_json()

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Look up user in database
    user = get_user(username)
    if not user:
        return jsonify({"error": "Invalid username or password"}), 401

    # Verify password against stored hash
    if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        # Create session
        session["username"] = username
        logger.info(f"User logged in: {username}")
        return jsonify({
            "message": "Login successful",
            "username": username
        }), 200
    else:
        logger.warning(f"Failed login attempt for: {username}")
        return jsonify({"error": "Invalid username or password"}), 401


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    """Log out the current user by clearing the session."""
    username = session.pop("username", None)
    if username:
        logger.info(f"User logged out: {username}")
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/api/me", methods=["GET"])
def get_current_user():
    """Return the currently logged-in user's info."""
    if "username" in session:
        return jsonify({"username": session["username"]}), 200
    return jsonify({"error": "Not logged in"}), 401
