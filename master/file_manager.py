"""
File Manager
-------------
Core module that handles file upload, download, and deletion.
Implements file chunking, distribution, and reconstruction.

Upload Flow:
    1. Receive file from client
    2. Split file into fixed-size chunks (CHUNK_SIZE bytes)
    3. For each chunk:
       a. Select primary node via load balancer
       b. Send chunk to primary node
       c. Replicate chunk to (REPLICATION_FACTOR - 1) additional nodes
       d. Save chunk metadata and locations to database
    4. Save file metadata to database

Download Flow:
    1. Look up file metadata in database
    2. For each chunk (ordered by index):
       a. Find healthy node that has this chunk
       b. Download chunk data from that node
    3. Merge all chunks in order
    4. Return the complete file

Delete Flow:
    1. Look up all chunk locations from database
    2. Send delete request to each storage node
    3. Remove all metadata from database
"""

import uuid
import io
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Blueprint, request, jsonify, session, send_file
from config import CHUNK_SIZE, MAX_FILE_SIZE, REPLICATION_FACTOR, STORAGE_NODES
from metadata import (
    save_file_metadata, get_file_metadata, get_user_files,
    delete_file_metadata, save_chunk_metadata, save_chunk_location,
    get_chunk_locations, get_file_chunks
)
from load_balancer import load_balancer
from replicator import replicate_chunk
from health_monitor import get_healthy_nodes, is_node_healthy
from auth import login_required
from logger_config import setup_logger

# Create Flask Blueprint for file routes
file_bp = Blueprint("files", __name__)
logger = setup_logger("file_manager")


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def split_file_into_chunks(file_data):
    """
    Split raw file bytes into fixed-size chunks.

    Args:
        file_data: Raw bytes of the uploaded file

    Returns:
        List of byte chunks, each up to CHUNK_SIZE bytes

    Example:
        A 650 KB file with CHUNK_SIZE=256 KB → 3 chunks:
        [256 KB, 256 KB, 138 KB]
    """
    chunks = []
    for i in range(0, len(file_data), CHUNK_SIZE):
        chunk = file_data[i:i + CHUNK_SIZE]
        chunks.append(chunk)
    return chunks


def send_chunk_to_node(chunk_data, chunk_id, node):
    """
    Send a chunk to a specific storage node via HTTP POST.

    Args:
        chunk_data: Raw bytes of the chunk
        chunk_id: Unique chunk identifier
        node: Node dict with host and port

    Returns:
        True if chunk was stored successfully, False otherwise
    """
    try:
        url = f"http://{node['host']}:{node['port']}/store_chunk"
        files = {"chunk": (chunk_id, io.BytesIO(chunk_data))}
        data = {"chunk_id": chunk_id}

        response = requests.post(url, files=files, data=data, timeout=10)
        return response.status_code == 200

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send chunk {chunk_id} to {node['node_id']}: {str(e)}")
        return False


def retrieve_chunk_from_node(chunk_id, node):
    """
    Retrieve a chunk from a specific storage node.

    Args:
        chunk_id: The chunk to retrieve
        node: Node dict with host and port

    Returns:
        Raw bytes of the chunk, or None if retrieval failed
    """
    try:
        url = f"http://{node['host']}:{node['port']}/get_chunk/{chunk_id}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            return response.content
        else:
            logger.warning(f"Chunk {chunk_id} not found on {node['node_id']}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve chunk {chunk_id} from {node['node_id']}: {str(e)}")
        return None


def delete_chunk_from_node(chunk_id, node_id):
    """
    Delete a chunk from a specific storage node.

    Args:
        chunk_id: The chunk to delete
        node_id: ID of the node to delete from
    """
    # Find node config by ID
    node = next((n for n in STORAGE_NODES if n["node_id"] == node_id), None)
    if not node:
        return

    try:
        url = f"http://{node['host']}:{node['port']}/delete_chunk/{chunk_id}"
        requests.delete(url, timeout=10)
        logger.info(f"Deleted chunk {chunk_id} from {node_id}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not delete chunk {chunk_id} from {node_id}: {str(e)}")


def process_chunk(chunk_data, chunk_id, file_id, index, healthy_nodes):
    """
    Process a single chunk: store on primary node and replicate to others.
    Runs in a separate thread during parallel upload.
    """
    try:
        # Step 1: Select primary node using round-robin load balancer
        primary_node = load_balancer.get_next_node(healthy_nodes)
        if not primary_node:
            return False, f"No healthy nodes available for chunk {index}"

        # Step 2: Send chunk to primary node
        success = send_chunk_to_node(chunk_data, chunk_id, primary_node)
        if not success:
            return False, f"Failed to store chunk {index} on primary node {primary_node['node_id']}"

        # Step 3: Save chunk metadata
        save_chunk_metadata(chunk_id, file_id, index, len(chunk_data))
        save_chunk_location(chunk_id, primary_node["node_id"], is_primary=True)

        # Step 4: Replicate to additional nodes
        replica_nodes = load_balancer.get_replica_nodes(
            primary_node, healthy_nodes, REPLICATION_FACTOR
        )
        if replica_nodes:
            successful_replicas = replicate_chunk(
                chunk_data, chunk_id, primary_node, replica_nodes
            )
            # Record replica locations in metadata
            for replica_node_id in successful_replicas:
                save_chunk_location(chunk_id, replica_node_id, is_primary=False)

        return True, None
    except Exception as e:
        return False, str(e)


# ──────────────────────────────────────────────
# API Endpoints
# ──────────────────────────────────────────────

@file_bp.route("/api/upload", methods=["POST"])
@login_required
def upload_file():
    """
    Upload a file to the distributed storage system.

    Process:
        1. Validate the uploaded file
        2. Split into chunks
        3. Distribute chunks across storage nodes (PARALLEL)
        4. Replicate each chunk for fault tolerance (PARALLEL)
        5. Store metadata in database
    """
    # Get the uploaded file
    uploaded_file = request.files.get("file")
    if not uploaded_file or uploaded_file.filename == "":
        return jsonify({"error": "No file provided"}), 400

    # Read file data
    file_data = uploaded_file.read()
    file_size = len(file_data)

    # Check file size limit
    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        return jsonify({"error": f"File too large. Maximum size is {max_mb} MB"}), 413

    # Check if there are healthy nodes available
    healthy_nodes = get_healthy_nodes()
    if not healthy_nodes:
        return jsonify({"error": "No storage nodes available. System is down."}), 503

    if len(healthy_nodes) < REPLICATION_FACTOR:
        logger.warning(
            f"Only {len(healthy_nodes)} healthy nodes available, "
            f"but replication factor is {REPLICATION_FACTOR}"
        )

    # Generate unique file ID
    file_id = str(uuid.uuid4())
    original_name = uploaded_file.filename
    owner = session["username"]

    # Split file into chunks
    chunks = split_file_into_chunks(file_data)
    chunk_count = len(chunks)

    logger.info(
        f"Uploading '{original_name}' ({file_size} bytes, {chunk_count} chunks) "
        f"by user '{owner}' — PARALLEL mode"
    )

    # Use ThreadPoolExecutor to process chunks in parallel
    errors = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_chunk = {
            executor.submit(
                process_chunk, chunk_data, f"{file_id}_chunk_{index}", file_id, index, healthy_nodes
            ): index
            for index, chunk_data in enumerate(chunks)
        }

        for future in as_completed(future_to_chunk):
            index = future_to_chunk[future]
            try:
                success, error_msg = future.result()
                if not success:
                    errors.append(f"Chunk {index}: {error_msg}")
            except Exception as e:
                errors.append(f"Chunk {index}: Unexpected error {str(e)}")

    if errors:
        logger.error(f"Upload failed with {len(errors)} errors: {errors[0]}...")
        return jsonify({"error": "Failed to store some file chunks", "details": errors}), 500

    # Save file metadata
    save_file_metadata(file_id, original_name, file_size, chunk_count, owner)

    logger.info(f"File upload complete: {original_name} (ID: {file_id})")
    return jsonify({
        "message": "File uploaded successfully",
        "file_id": file_id,
        "filename": original_name,
        "size": file_size,
        "chunks": chunk_count,
        "replication_factor": REPLICATION_FACTOR
    }), 200


def fetch_chunk_with_retry(chunk_meta):
    """
    Fetch a single chunk from storage nodes with fault tolerance.
    Tries primary node first, then replicas if needed.
    """
    chunk_id = chunk_meta["chunk_id"]
    chunk_index = chunk_meta["chunk_index"]
    locations = get_chunk_locations(chunk_id)

    # Try each location until we successfully retrieve the chunk
    for location in locations:
        node_id = location["node_id"]

        # Skip unhealthy nodes
        if not is_node_healthy(node_id):
            logger.warning(
                f"Skipping {node_id} for chunk {chunk_id} (node is down). "
                f"Trying replica..."
            )
            continue

        # Find full node config
        node = next((n for n in STORAGE_NODES if n["node_id"] == node_id), None)
        if not node:
            continue

        # Try retrieving the chunk
        chunk_data = retrieve_chunk_from_node(chunk_id, node)
        if chunk_data:
            logger.info(f"Retrieved chunk {chunk_index} from {node_id} (Parallel Mode)")
            return chunk_index, chunk_data

    logger.error(f"FATAL: Could not retrieve chunk {chunk_id} from any node!")
    return chunk_index, None


@file_bp.route("/api/download/<file_id>", methods=["GET"])
@login_required
def download_file(file_id):
    """
    Download a file by reconstructing it from distributed chunks.

    Process:
        1. Look up file metadata
        2. For each chunk, find a healthy node that has it
        3. Download all chunks IN PARALLEL
        4. Merge chunks in the correct index order
        5. Send the complete file to client
    """
    # Look up file metadata
    file_meta = get_file_metadata(file_id)
    if not file_meta:
        return jsonify({"error": "File not found"}), 404

    # Verify ownership
    if file_meta["owner"] != session["username"]:
        return jsonify({"error": "Access denied"}), 403

    logger.info(f"Downloading file: {file_meta['original_name']} (ID: {file_id}) — PARALLEL mode")

    # Get all chunks for this file (ordered by index)
    chunks_meta = get_file_chunks(file_id)
    if not chunks_meta:
        return jsonify({"error": "No chunks found for this file"}), 404

    # Reconstruct the file by downloading chunks in parallel
    chunk_results = {}
    errors = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_chunk = {
            executor.submit(fetch_chunk_with_retry, cm): cm["chunk_index"]
            for cm in chunks_meta
        }

        for future in as_completed(future_to_chunk):
            index = future_to_chunk[future]
            try:
                chunk_index, chunk_data = future.result()
                if chunk_data is None:
                    errors.append(f"Failed to retrieve chunk {index}")
                else:
                    chunk_results[chunk_index] = chunk_data
            except Exception as e:
                errors.append(f"Unexpected error retrieving chunk {index}: {str(e)}")

    if errors:
        logger.error(f"Download failed with {len(errors)} errors: {errors[0]}")
        return jsonify({
            "error": "One or more file chunks are unavailable. All nodes storing them are down."
        }), 503

    # Merge chunks in the correct order
    file_data = bytearray()
    for i in range(len(chunks_meta)):
        file_data.extend(chunk_results[i])

    # Send the reconstructed file
    logger.info(
        f"File download complete: {file_meta['original_name']} "
        f"({len(file_data)} bytes reconstructed in parallel)"
    )

    return send_file(
        io.BytesIO(file_data),
        download_name=file_meta["original_name"],
        as_attachment=True
    )


@file_bp.route("/api/files", methods=["GET"])
@login_required
def list_files():
    """
    List all files uploaded by the current user.
    Returns file metadata including name, size, date, chunk count.
    """
    username = session["username"]
    files = get_user_files(username)

    # Format file sizes for display
    for f in files:
        size = f["file_size"]
        if size < 1024:
            f["size_display"] = f"{size} B"
        elif size < 1024 * 1024:
            f["size_display"] = f"{size / 1024:.1f} KB"
        else:
            f["size_display"] = f"{size / (1024 * 1024):.2f} MB"

    return jsonify({"files": files}), 200


@file_bp.route("/api/delete/<file_id>", methods=["DELETE"])
@login_required
def delete_file(file_id):
    """
    Delete a file from the distributed storage system.

    Process:
        1. Verify file exists and user owns it
        2. Get all chunk locations from metadata
        3. Delete chunks from all storage nodes
        4. Remove all metadata from database
    """
    # Look up file metadata
    file_meta = get_file_metadata(file_id)
    if not file_meta:
        return jsonify({"error": "File not found"}), 404

    # Verify ownership
    if file_meta["owner"] != session["username"]:
        return jsonify({"error": "Access denied"}), 403

    logger.info(f"Deleting file: {file_meta['original_name']} (ID: {file_id})")

    # Get chunk locations before deleting metadata
    chunks_meta = get_file_chunks(file_id)
    for chunk_meta in chunks_meta:
        chunk_id = chunk_meta["chunk_id"]
        locations = get_chunk_locations(chunk_id)

        # Delete from each storage node
        for location in locations:
            delete_chunk_from_node(chunk_id, location["node_id"])

    # Delete all metadata
    delete_file_metadata(file_id)

    logger.info(f"File deleted: {file_meta['original_name']}")
    return jsonify({"message": "File deleted successfully"}), 200
