# Diagrams — Distributed File Storage System

## 1. DFD Level 0 (Context Diagram)

```mermaid
graph LR
    U["👤 User"] -->|Upload/Download/Delete| S["☁️ Distributed File Storage System"]
    S -->|File Data| U
    S <-->|Store/Retrieve Chunks| N1["🖥️ Storage Node 1"]
    S <-->|Store/Retrieve Chunks| N2["🖥️ Storage Node 2"]
    S <-->|Store/Retrieve Chunks| N3["🖥️ Storage Node 3"]
```

**Description:**  
The user interacts with the Distributed File Storage System to upload, download, and delete files. Internally, the system distributes file chunks across multiple storage nodes.

---

## 2. DFD Level 1 (Detailed)

```mermaid
graph TD
    U["👤 User"] -->|Login/Signup| P1["1.0 Authentication"]
    P1 -->|Session| P2["2.0 File Upload"]
    P1 -->|Session| P3["3.0 File Download"]
    P1 -->|Session| P4["4.0 File Delete"]

    U -->|File| P2
    P2 -->|Split into Chunks| P5["5.0 Chunk Distributor"]
    P5 -->|Select Node| P6["6.0 Load Balancer"]
    P6 -->|Primary Node| P5
    P5 -->|Store Chunk| N["🖥️ Storage Nodes"]
    P5 -->|Replicate| P7["7.0 Replicator"]
    P7 -->|Copy Chunk| N
    P5 -->|Save Metadata| DB["🗄️ SQLite Database"]

    U -->|Request File| P3
    P3 -->|Lookup Chunks| DB
    P3 -->|Get Chunks| N
    P3 -->|Merge Chunks| U

    U -->|Delete Request| P4
    P4 -->|Find Chunks| DB
    P4 -->|Delete Chunks| N
    P4 -->|Remove Metadata| DB

    P8["8.0 Health Monitor"] -->|Ping| N
    P8 -->|Update Status| DB
```

---

## 3. Class Diagram

```mermaid
classDiagram
    class MasterNode {
        -Flask app
        -secret_key: str
        +serve_frontend()
        +init_database()
        +start_health_monitor()
    }

    class AuthModule {
        +signup(username, password)
        +login(username, password)
        +logout()
        +get_current_user()
        -login_required() decorator
    }

    class FileManager {
        +upload_file(file)
        +download_file(file_id)
        +delete_file(file_id)
        +list_files(username)
        -split_file_into_chunks(data)
        -send_chunk_to_node(chunk, node)
        -retrieve_chunk_from_node(chunk_id, node)
        -delete_chunk_from_node(chunk_id, node_id)
    }

    class MetadataManager {
        -db_path: str
        +init_database()
        +create_user(username, hash)
        +get_user(username)
        +save_file_metadata(...)
        +get_file_metadata(file_id)
        +get_user_files(username)
        +delete_file_metadata(file_id)
        +save_chunk_metadata(...)
        +save_chunk_location(...)
        +get_chunk_locations(chunk_id)
        +get_file_chunks(file_id)
    }

    class LoadBalancer {
        -_current_index: int
        -_lock: Lock
        +get_next_node(healthy_nodes)
        +get_replica_nodes(primary, nodes, factor)
    }

    class Replicator {
        +replicate_chunk(data, id, primary, replicas)
    }

    class HealthMonitor {
        -node_status: dict
        -disabled_nodes: set
        +start_health_monitor()
        +get_healthy_nodes()
        +is_node_healthy(node_id)
        +toggle_node(node_id)
        -check_node_health(node)
        -health_check_loop()
    }

    class StorageNode {
        -NODE_ID: str
        -PORT: int
        -STORAGE_DIR: str
        +store_chunk(chunk_id, data)
        +get_chunk(chunk_id)
        +delete_chunk(chunk_id)
        +health_check()
        +node_status()
    }

    MasterNode --> AuthModule
    MasterNode --> FileManager
    MasterNode --> HealthMonitor
    FileManager --> MetadataManager
    FileManager --> LoadBalancer
    FileManager --> Replicator
    FileManager --> StorageNode : REST API
    HealthMonitor --> StorageNode : REST API
    Replicator --> StorageNode : REST API
```

---

## 4. Sequence Diagram — File Upload

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Master
    participant LoadBalancer
    participant Node1
    participant Node2
    participant DB as SQLite DB

    User->>Frontend: Select file to upload
    Frontend->>Master: POST /api/upload (file)
    Master->>Master: Split file into chunks

    loop For each chunk
        Master->>LoadBalancer: get_next_node()
        LoadBalancer-->>Master: Selected node (round-robin)
        Master->>Node1: POST /store_chunk (chunk_data)
        Node1-->>Master: 200 OK

        Master->>LoadBalancer: get_replica_nodes()
        LoadBalancer-->>Master: Replica node list
        Master->>Node2: POST /store_chunk (replica)
        Node2-->>Master: 200 OK

        Master->>DB: Save chunk metadata & locations
    end

    Master->>DB: Save file metadata
    Master-->>Frontend: 200 OK (file_id, chunks, etc.)
    Frontend-->>User: Upload complete notification
```

---

## 5. Sequence Diagram — File Download (with Fault Tolerance)

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Master
    participant DB as SQLite DB
    participant Node1
    participant Node2 as Node2 (DOWN)
    participant Node3

    User->>Frontend: Click Download
    Frontend->>Master: GET /api/download/{file_id}
    Master->>DB: Get file metadata
    DB-->>Master: File info + chunk list

    loop For each chunk
        Master->>DB: Get chunk locations
        DB-->>Master: [Node1, Node2]

        alt Node1 is healthy
            Master->>Node1: GET /get_chunk/{id}
            Node1-->>Master: chunk data
        else Node1 is down, try replica
            Master->>Node2: GET /get_chunk/{id}
            Note over Node2: Connection refused!
            Master->>Node3: GET /get_chunk/{id} (replica)
            Node3-->>Master: chunk data
        end
    end

    Master->>Master: Merge all chunks
    Master-->>Frontend: Complete file (binary)
    Frontend-->>User: File download starts
```

---

## 6. Sequence Diagram — Health Monitoring

```mermaid
sequenceDiagram
    participant Monitor as Health Monitor Thread
    participant Node1
    participant Node2
    participant Node3
    participant Status as Node Status Registry

    loop Every 10 seconds
        Monitor->>Node1: GET /health
        Node1-->>Monitor: 200 OK (healthy)
        Monitor->>Status: Update node1 = healthy

        Monitor->>Node2: GET /health
        Note over Node2: Timeout!
        Monitor->>Status: Update node2 = dead ⚠️

        Monitor->>Node3: GET /health
        Node3-->>Monitor: 200 OK (healthy)
        Monitor->>Status: Update node3 = healthy
    end
```
