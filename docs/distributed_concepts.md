# Distributed Computing Concepts — Implementation Details

This document explains how each distributed computing concept is implemented in the CloudVault system.

---

## 1. Replication

### Concept
Replication is the process of storing multiple copies of data on different nodes to ensure data availability and durability.

### Implementation
- **Replication Factor**: Configurable (default = 2). Each chunk is stored on 2 different nodes.
- **Module**: `replicator.py`
- **Process**:
  1. When a chunk is stored on its primary node, the replicator immediately copies it to additional nodes.
  2. Replica nodes are selected by the load balancer, excluding the primary node.
  3. The chunk metadata in SQLite tracks which nodes hold each chunk copy.

### Code Reference
```python
# In file_manager.py (upload flow)
# Step 1: Store on primary node
success = send_chunk_to_node(chunk_data, chunk_id, primary_node)

# Step 2: Replicate to additional nodes
replica_nodes = load_balancer.get_replica_nodes(primary_node, healthy_nodes, REPLICATION_FACTOR)
successful_replicas = replicate_chunk(chunk_data, chunk_id, primary_node, replica_nodes)
```

### Why It Matters
Without replication, if a node fails, all data on that node is lost. With replication factor 2, we can tolerate 1 node failure without data loss.

---

## 2. Fault Tolerance

### Concept
Fault tolerance is the ability of a system to continue operating even when some components fail.

### Implementation
- **Module**: `health_monitor.py` + `file_manager.py` (download logic)
- **Node Health Monitoring**: Background thread pings each storage node every 10 seconds via `/health` endpoint.
- **Fault-Tolerant Download**: During file download, if the primary node for a chunk is down, the system automatically retrieves the chunk from a replica node.
- **Node Simulation**: The dashboard allows manually toggling nodes on/off to demonstrate fault tolerance.

### Code Reference
```python
# In file_manager.py (download flow)
for location in locations:
    node_id = location["node_id"]

    # Skip unhealthy nodes
    if not is_node_healthy(node_id):
        logger.warning(f"Skipping {node_id} (node is down). Trying replica...")
        continue

    # Try retrieving from this node
    chunk_data = retrieve_chunk_from_node(chunk_id, node)
    if chunk_data:
        break  # Got it from a replica!
```

### Demo Scenario
1. Upload a file (chunks distributed to Node1 and Node2)
2. Toggle Node1 OFF from the dashboard
3. Download the file — system automatically retrieves chunks from Node2 (replica)
4. File downloads successfully despite Node1 being down ✅

---

## 3. Consistency

### Concept
Consistency ensures that all nodes see the same data at the same time. In distributed systems, there's often a trade-off between consistency, availability, and partition tolerance (CAP theorem).

### Implementation
- **Strategy**: Strong consistency via centralized metadata (Master node holds the single source of truth).
- **Module**: `metadata.py` (SQLite database)
- **How It Works**:
  - All metadata (file locations, chunk mappings) is stored in a single SQLite database on the master node.
  - Before any operation (upload/download/delete), the master consults the metadata to determine exact chunk locations.
  - SQLite uses WAL (Write-Ahead Logging) mode for better concurrent access.

### Trade-off
This is a form of **strong consistency** — there's no conflict between nodes because all metadata operations go through the master. The trade-off is that if the master fails, the entire system is unavailable (single point of failure). In a production system, the master itself would be replicated.

---

## 4. Distributed Communication

### Concept
Nodes in a distributed system need to communicate with each other to coordinate operations.

### Implementation
- **Protocol**: HTTP REST APIs
- **Library**: Python `requests` library for inter-node communication
- **Communication Flows**:

| From | To | Method | Endpoint | Purpose |
|------|----|--------|----------|---------|
| Master | Storage Node | POST | `/store_chunk` | Store a chunk |
| Master | Storage Node | GET | `/get_chunk/<id>` | Retrieve a chunk |
| Master | Storage Node | DELETE | `/delete_chunk/<id>` | Delete a chunk |
| Master | Storage Node | GET | `/health` | Health check |
| Master | Storage Node | GET | `/status` | Get node stats |
| Frontend | Master | POST | `/api/upload` | Upload file |
| Frontend | Master | GET | `/api/download/<id>` | Download file |
| Frontend | Master | DELETE | `/api/delete/<id>` | Delete file |

### Why REST?
REST APIs are:
- Language-agnostic (nodes could be in different languages)
- Easy to test and debug (curl, Postman)
- Based on HTTP (well-understood protocol)
- Stateless (each request is independent)

---

## 5. Load Balancing (Round-Robin)

### Concept
Load balancing distributes workload evenly across multiple nodes to prevent any single node from becoming a bottleneck.

### Implementation
- **Algorithm**: Round-Robin
- **Module**: `load_balancer.py`
- **How It Works**:
  1. Maintain a rotating index counter
  2. For each new chunk, assign it to the next node in sequence
  3. Skip unhealthy nodes
  4. Thread-safe using a lock

```python
# Round-robin: each chunk goes to the next node in sequence
# Chunk 0 → Node 1
# Chunk 1 → Node 2
# Chunk 2 → Node 3
# Chunk 3 → Node 1 (wraps around)
# ...
```

---

## 6. File Chunking

### Concept
Large files are split into smaller fixed-size pieces (chunks) for distributed storage.

### Implementation
- **Chunk Size**: 256 KB (configurable in `config.py`)
- **Process**:
  1. Read the entire file as bytes
  2. Split into chunks of `CHUNK_SIZE` bytes each
  3. Last chunk may be smaller than `CHUNK_SIZE`
  4. Each chunk gets a unique ID: `{file_uuid}_chunk_{index}`

### Example
A 650 KB file → 3 chunks:
- Chunk 0: 256 KB → stored on Node 1, replicated to Node 2
- Chunk 1: 256 KB → stored on Node 2, replicated to Node 3
- Chunk 2: 138 KB → stored on Node 3, replicated to Node 1

---

## CAP Theorem Analysis

This system prioritizes **Consistency** and **Availability** over Partition Tolerance:

| Property | Status | Explanation |
|----------|--------|-------------|
| **Consistency** | ✅ Strong | Centralized metadata (single SQLite DB) |
| **Availability** | ✅ Partial | System works if master + at least 1 storage node is up |
| **Partition Tolerance** | ⚠️ Limited | Master is a single point of failure |

In a production system (like Google's GFS), the master itself would also be replicated for full partition tolerance.
