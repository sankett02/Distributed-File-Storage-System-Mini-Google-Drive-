# Architecture — Distributed File Storage System

## High-Level Architecture

The system follows a **Master-Slave (Coordinator-Worker)** architecture, which is a common pattern in distributed systems like HDFS, GFS, and Google Drive.

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                         │
│              HTML/CSS/JS Dashboard — Port 5000                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP REST API
┌──────────────────────────▼──────────────────────────────────────┐
│                     MASTER NODE (Port 5000)                      │
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │   Auth       │   │   Metadata   │   │   File Manager       │ │
│  │   Module     │   │   Manager    │   │   (Chunking +        │ │
│  │              │   │   (SQLite)   │   │    Distribution)     │ │
│  └──────────────┘   └──────────────┘   └──────────────────────┘ │
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │   Load       │   │   Health     │   │   Replicator         │ │
│  │   Balancer   │   │   Monitor   │   │                      │ │
│  │  (Round-Robin)│   │  (Background)│   │                      │ │
│  └──────────────┘   └──────────────┘   └──────────────────────┘ │
└──────┬──────────────────┬──────────────────┬────────────────────┘
       │                  │                  │
    HTTP REST          HTTP REST          HTTP REST
       │                  │                  │
┌──────▼─────┐     ┌──────▼─────┐     ┌──────▼─────┐
│  STORAGE   │     │  STORAGE   │     │  STORAGE   │
│  NODE 1    │     │  NODE 2    │     │  NODE 3    │
│  Port 5001 │     │  Port 5002 │     │  Port 5003 │
│            │     │            │     │            │
│  Flask     │     │  Flask     │     │  Flask     │
│  Server    │     │  Server    │     │  Server    │
│            │     │            │     │            │
│ /storage/  │     │ /storage/  │     │ /storage/  │
│  node1/    │     │  node2/    │     │  node3/    │
└────────────┘     └────────────┘     └────────────┘
```

## Component Details

### 1. Master Node (Coordinator)
The master node is the brain of the system. It does NOT store file data — it only manages metadata and coordinates operations.

**Responsibilities:**
- Accept file uploads from clients
- Split files into chunks
- Decide which storage nodes to use (load balancing)
- Manage replication
- Track file/chunk metadata in SQLite
- Monitor storage node health
- Handle user authentication

### 2. Storage Nodes (Workers)
Each storage node is an independent Flask server that stores raw file chunks on its local filesystem.

**Responsibilities:**
- Store chunks received from the master
- Serve chunks on request
- Delete chunks when instructed
- Respond to health checks

### 3. Frontend (Client)
A browser-based UI that communicates with the master node via REST APIs.

**Features:**
- Login / Signup
- File upload with progress tracking
- File listing and management
- Node status dashboard
- Fault simulation controls

## Data Flow

### Upload Flow
```
Client                 Master               Node1    Node2    Node3
  │                      │                    │        │        │
  │──── Upload File ────>│                    │        │        │
  │                      │                    │        │        │
  │                      │── Split into       │        │        │
  │                      │   chunks           │        │        │
  │                      │                    │        │        │
  │                      │── Chunk 0 ────────>│        │        │
  │                      │── Replicate 0 ─────────────>│        │
  │                      │                    │        │        │
  │                      │── Chunk 1 ─────────────────>│        │
  │                      │── Replicate 1 ──────────────────────>│
  │                      │                    │        │        │
  │                      │── Save metadata    │        │        │
  │<──── Success ────────│                    │        │        │
```

### Download Flow (with Fault Tolerance)
```
Client                 Master               Node1    Node2(DOWN)  Node3
  │                      │                    │        │           │
  │── Download File ────>│                    │        │           │
  │                      │── Lookup metadata  │        │           │
  │                      │                    │        │           │
  │                      │── Get Chunk 0 ────>│        │           │
  │                      │<── Chunk 0 ────────│        │           │
  │                      │                    │        │           │
  │                      │── Get Chunk 1 ─────────────>│ FAIL!    │
  │                      │── Try Replica ────────────────────────>│
  │                      │<── Chunk 1 ────────────────────────────│
  │                      │                    │        │           │
  │                      │── Merge chunks     │        │           │
  │<──── Complete File ──│                    │        │           │
```

## Database Schema

```
┌────────────────────────────────────────────────────────┐
│                        SQLite DB                        │
├────────────────┬───────────────────────────────────────┤
│     users      │  id, username, password_hash,         │
│                │  created_at                           │
├────────────────┼───────────────────────────────────────┤
│     files      │  id, file_id, original_name,          │
│                │  file_size, chunk_count, owner,       │
│                │  created_at                           │
├────────────────┼───────────────────────────────────────┤
│     chunks     │  id, chunk_id, file_id,               │
│                │  chunk_index, chunk_size              │
├────────────────┼───────────────────────────────────────┤
│ chunk_locations│  id, chunk_id, node_id,               │
│                │  is_primary, created_at               │
└────────────────┴───────────────────────────────────────┘
```

## Communication Protocol

All inter-node communication uses **HTTP REST APIs**:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/store_chunk` | POST | Store a chunk on a storage node |
| `/get_chunk/<id>` | GET | Retrieve a chunk from a storage node |
| `/delete_chunk/<id>` | DELETE | Delete a chunk from a storage node |
| `/health` | GET | Health check (returns 200 if alive) |
| `/status` | GET | Detailed node statistics |
