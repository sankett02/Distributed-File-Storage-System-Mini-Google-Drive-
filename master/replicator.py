"""
Replicator Module
-----------------
Handles file chunk replication across storage nodes.
Ensures each chunk has multiple copies for fault tolerance.

Replication Strategy:
    1. After a chunk is stored on the primary node, the replicator
       copies it to (REPLICATION_FACTOR - 1) additional nodes.
    2. Replicas are selected from healthy nodes (excluding the primary).
    3. If a node is down during replication, it is skipped (logged as warning).
"""

import requests
import io
from config import REPLICATION_FACTOR
from logger_config import setup_logger

logger = setup_logger("replicator")


def replicate_chunk(chunk_data, chunk_id, primary_node, replica_nodes):
    """
    Replicate a chunk from the primary node to replica nodes.

    Args:
        chunk_data: Raw bytes of the chunk
        chunk_id: Unique identifier for the chunk
        primary_node: Node dict where primary copy is stored
        replica_nodes: List of node dicts to replicate to

    Returns:
        List of node_ids where replication succeeded
    """
    successful_replicas = []

    for node in replica_nodes:
        try:
            url = f"http://{node['host']}:{node['port']}/store_chunk"

            # Send chunk data as multipart form
            files = {"chunk": (chunk_id, io.BytesIO(chunk_data))}
            data = {"chunk_id": chunk_id}

            response = requests.post(url, files=files, data=data, timeout=10)

            if response.status_code == 200:
                successful_replicas.append(node["node_id"])
                logger.info(
                    f"Chunk {chunk_id} replicated to {node['node_id']} "
                    f"(port {node['port']})"
                )
            else:
                logger.warning(
                    f"Failed to replicate chunk {chunk_id} to {node['node_id']}: "
                    f"Status {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Replication error for chunk {chunk_id} to {node['node_id']}: {str(e)}"
            )

    # Log replication summary
    total_copies = 1 + len(successful_replicas)  # primary + replicas
    logger.info(
        f"Chunk {chunk_id}: {total_copies}/{REPLICATION_FACTOR} copies "
        f"(primary: {primary_node['node_id']}, replicas: {successful_replicas})"
    )

    return successful_replicas
