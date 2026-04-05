# Viva Questions & Answers — Distributed Computing

> Mumbai University • B.E. Computer Engineering • Semester 8

---

## 1. What is a Distributed File Storage System?

**Answer:** A Distributed File Storage System is a system that stores files across multiple networked machines (nodes) rather than on a single machine. Files are split into smaller pieces (chunks), distributed across nodes, and replicated for fault tolerance. Examples include Google File System (GFS), Hadoop Distributed File System (HDFS), and Amazon S3.

---

## 2. Why did you choose a Master-Slave architecture?

**Answer:** We chose Master-Slave (Coordinator-Worker) architecture because:
- It simplifies metadata management — the master is the single source of truth
- It makes consistency easier to maintain
- It's the same architecture used by GFS and HDFS
- It's simpler to implement compared to peer-to-peer architectures
- The trade-off is that the master is a single point of failure, which in production systems is solved by replicating the master itself

---

## 3. What is file chunking and why is it needed?

**Answer:** File chunking is the process of splitting a large file into smaller fixed-size pieces (chunks). In our system, we use 256 KB chunks.

**Why it's needed:**
- Enables parallel storage across multiple nodes
- Allows better load balancing (chunks can go to different nodes)
- Enables partial file recovery (if some chunks are lost, others can still be retrieved)
- Reduces the impact of network failures (smaller transfers are more reliable)

---

## 4. Explain the replication mechanism in your project.

**Answer:** Our system uses a configurable replication factor (default = 2). When a file is uploaded:
1. Each chunk is first stored on a primary node (selected by the load balancer)
2. The replicator then copies each chunk to (replication_factor - 1) additional nodes
3. The metadata database records all chunk locations

With replication factor 2 and 3 nodes, each chunk exists on 2 different nodes. This means the system can tolerate 1 node failure without any data loss.

---

## 5. How does your system handle node failures (fault tolerance)?

**Answer:** Fault tolerance is implemented at multiple levels:
1. **Replication**: Each chunk is stored on multiple nodes
2. **Health Monitoring**: A background thread pings storage nodes every 10 seconds
3. **Fault-tolerant Download**: When downloading, if the primary node for a chunk is down, the system automatically retrieves the chunk from a replica node
4. **Node Status Tracking**: The master maintains a real-time registry of healthy/dead nodes

---

## 6. What is the CAP theorem? How does it apply to your project?

**Answer:** The CAP theorem states that a distributed system can provide at most two of three guarantees:
- **C (Consistency)**: Every read receives the most recent write
- **A (Availability)**: Every request receives a response
- **P (Partition Tolerance)**: The system continues to operate despite network partitions

Our system prioritizes **Consistency** and **Availability** (CA):
- **Consistency**: Centralized metadata in SQLite ensures all operations see the same state
- **Availability**: Replication ensures data is available even if some nodes fail
- **Partition Tolerance**: Limited, because the master is a single point of failure

---

## 7. What load balancing algorithm did you use and why?

**Answer:** We used **Round-Robin** load balancing:
- It assigns chunks to nodes in a rotating sequence (Node1 → Node2 → Node3 → Node1 → ...)
- It ensures even distribution of data across all nodes
- It's simple to implement and explain
- It skips unhealthy nodes automatically

Other algorithms we could have used: Random, Weighted Round-Robin, Least Connections, Consistent Hashing.

---

## 8. How is consistency maintained in your system?

**Answer:** Consistency is maintained through **centralized metadata management**:
- All metadata (file records, chunk locations) is stored in a single SQLite database on the master node
- Every operation (upload, download, delete) goes through the master, which consults the database
- SQLite uses WAL (Write-Ahead Logging) mode for concurrent access
- This is a form of **strong consistency** — there's no stale data problem

---

## 9. What is the role of the Master Node?

**Answer:** The Master Node (Coordinator) is responsible for:
1. **File Management**: Receiving uploads, splitting files, coordinating downloads
2. **Metadata Management**: Tracking which chunks are on which nodes
3. **Load Balancing**: Distributing chunks evenly across storage nodes
4. **Health Monitoring**: Checking if storage nodes are alive
5. **Replication**: Ensuring chunks are copied to multiple nodes
6. **Authentication**: Managing user accounts and sessions
7. **Serving the UI**: The frontend is served from the master node

The master does NOT store file data — only metadata.

---

## 10. What happens if the Master Node fails?

**Answer:** In our current implementation, the master is a single point of failure (SPOF). If it fails:
- No new uploads or downloads can happen
- No metadata can be accessed
- Storage nodes still have the data but can't coordinate

**In production systems**, this is solved by:
- Replicating the master node (leader-follower)
- Using consensus algorithms (Raft, Paxos) for master election
- Using distributed databases (like etcd, ZooKeeper) for metadata

---

## 11. What communication protocol do you use between nodes?

**Answer:** We use **HTTP REST APIs** for all inter-node communication:
- Master → Storage Node: Store/Get/Delete chunks, Health checks
- Frontend → Master: Upload/Download/Delete files, Authentication

REST was chosen because:
- It's language-agnostic
- Easy to test and debug
- Stateless (each request is independent)
- Well-supported by all programming languages

---

## 12. How does the health monitoring system work?

**Answer:** The health monitor runs as a **background daemon thread** in the master node:
1. Every 10 seconds, it sends a GET request to `/health` on each storage node
2. If a node responds with HTTP 200, it's marked as "healthy"
3. If the request times out or fails, the node is marked as "dead"
4. The status is stored in a global dictionary with timestamps
5. The frontend polls `/api/nodes` to display live node status

---

## 13. Explain the upload flow in your system.

**Answer:**
1. Client sends file to master via POST `/api/upload`
2. Master reads the file and splits it into 256 KB chunks
3. For each chunk:
   - Load balancer selects a primary node (round-robin)
   - Chunk is sent to the primary node via POST `/store_chunk`
   - Replicator copies the chunk to additional nodes
   - Metadata (chunk ID, file ID, locations) is saved to SQLite
4. File metadata (name, size, chunk count) is saved to SQLite
5. Success response is sent to the client

---

## 14. Explain the download flow (including fault tolerance).

**Answer:**
1. Client requests file via GET `/api/download/<file_id>`
2. Master looks up file metadata in SQLite
3. Master retrieves chunk list ordered by chunk index
4. For each chunk:
   - Get all node locations from metadata
   - Try to download from the first healthy node
   - If that node is down, try the next location (replica)
   - Continue until the chunk is retrieved
5. All chunks are merged in the correct order
6. Complete file is sent to the client

---

## 15. What is the difference between horizontal and vertical scaling?

**Answer:**
- **Vertical Scaling (Scale Up)**: Add more resources (CPU, RAM) to a single machine
- **Horizontal Scaling (Scale Out)**: Add more machines to the system

Our system uses **horizontal scaling** — we add more storage nodes to increase capacity. This is the preferred approach in distributed systems because:
- It's more cost-effective
- It provides better fault tolerance
- There's no single hardware limit
- It's what companies like Google and Amazon use

---

## 16. What database did you use and why?

**Answer:** We used **SQLite** for metadata storage:
- Zero configuration required (no separate database server)
- Single file database — easy to inspect and demo
- Supports SQL queries for complex metadata lookups
- Built into Python (no additional installation)
- WAL mode for concurrent access

In a production system, we would use a distributed database like MongoDB, CockroachDB, or etcd.

---

## 17. How do you handle concurrent uploads?

**Answer:** Concurrent uploads are handled through:
1. **Thread-safe load balancer**: Uses a threading lock to prevent race conditions in node selection
2. **SQLite WAL mode**: Allows multiple readers and one writer simultaneously
3. **Stateless storage nodes**: Each Flask instance handles requests independently
4. **Independent chunk storage**: Each chunk has a unique UUID-based ID, so concurrent uploads don't interfere with each other

---

## 18. What is the difference between your system and HDFS?

**Answer:**
| Feature | Our System | HDFS |
|---------|-----------|------|
| Architecture | Master-Slave | NameNode-DataNode |
| Chunk Size | 256 KB | 128 MB |
| Replication | Configurable (default 2) | Default 3 |
| Metadata | SQLite | In-memory on NameNode |
| Communication | REST API | Custom RPC |
| Scale | 3 nodes (demo) | 1000s of nodes |
| Language | Python | Java |

---

## 19. What security measures did you implement?

**Answer:**
1. **Password Hashing**: Using bcrypt (salted hash) — passwords are never stored in plain text
2. **Session Authentication**: Flask sessions with secret key
3. **Login Required**: Protected routes check for valid session
4. **File Ownership**: Users can only access their own files
5. **Input Validation**: Username/password length checks
6. **XSS Prevention**: HTML escaping in frontend

---

## 20. What are the limitations of your system?

**Answer:**
1. **Single Point of Failure**: Master node is a SPOF
2. **No Re-replication**: If a node dies permanently, lost replicas are not re-created on other nodes
3. **No Encryption**: Chunk data is stored and transferred unencrypted
4. **Synchronous Replication**: Replication happens during upload, which increases latency
5. **No File Versioning**: Overwriting a file is not supported
6. **Memory-based Upload**: Entire file is loaded into memory before chunking

---

## 21. How would you improve this system for production?

**Answer:**
1. Replicate the master node for high availability
2. Use consistent hashing instead of round-robin
3. Implement re-replication when a node permanently fails
4. Add encryption for data at rest and in transit
5. Implement async replication with eventual consistency
6. Use streaming for large file uploads (avoid loading into memory)
7. Add file versioning and deduplication
8. Use a distributed database (etcd, ZooKeeper) for metadata
9. Containerize with Docker and orchestrate with Kubernetes

---

## 22. What is consistent hashing?

**Answer:** Consistent hashing is a load balancing technique where both nodes and data are mapped onto a circular hash ring. When a node is added or removed, only the data mapped near that node needs to be redistributed — unlike round-robin where all mappings change.

**Advantages over Round-Robin:**
- Minimal redistribution when nodes change
- Better suited for dynamic clusters
- Used by Amazon DynamoDB, Cassandra, etc.

---

## 23. What is eventual consistency vs strong consistency?

**Answer:**
- **Strong Consistency**: Every read returns the latest write. Our system uses this (centralized metadata).
- **Eventual Consistency**: Replicas may temporarily have different data, but will converge to the same state eventually. Used by Amazon DynamoDB, DNS.

Trade-off: Strong consistency provides correctness but lower availability. Eventual consistency provides higher availability but may return stale data.

---

## 24. What is the Byzantine Generals Problem?

**Answer:** It's a fundamental problem in distributed computing where components may fail by giving conflicting information to different parts of the system (malicious behavior). A system is Byzantine Fault Tolerant (BFT) if it can handle such failures.

Our system handles **crash faults** (node going offline) but not Byzantine faults (malicious nodes sending wrong data). A blockchain is an example of a BFT system.

---

## 25. What are idempotent operations and why are they important?

**Answer:** An idempotent operation produces the same result no matter how many times it's executed. In our system:
- **GET /health** is idempotent — calling it 100 times gives the same result
- **DELETE /delete_chunk** is idempotent — deleting the same chunk twice doesn't cause errors
- This is important in distributed systems because network failures can cause retries, and idempotent operations ensure retries are safe

---

## 26. Explain the difference between synchronous and asynchronous replication.

**Answer:**
- **Synchronous**: Master waits for all replicas to confirm before responding to client. Pros: Strong consistency. Cons: Higher latency.
- **Asynchronous**: Master responds to client immediately, replication happens in background. Pros: Lower latency. Cons: Risk of data loss if primary fails before replication.

Our system uses **synchronous replication** — the upload response is sent only after all replicas are stored.

---

## 27. What is a heartbeat in distributed systems?

**Answer:** A heartbeat is a periodic signal sent from one node to another to indicate that it's still alive. In our system:
- The master sends a GET `/health` request to each storage node every 10 seconds
- If a node doesn't respond, it's marked as "dead"
- This is the mechanism that enables fault detection

---

## 28. How does your logging system work?

**Answer:** We implemented structured logging using Python's `logging` module:
- Logs are written to both the console and a file (`master/logs/master.log`)
- Each module has its own logger (auth, file_manager, health_monitor, etc.)
- Log format: `[MODULE] TIMESTAMP - LEVEL - Message`
- Log levels used: INFO (normal operations), WARNING (recoverable issues), ERROR (failures)

---

## 29. What is the difference between REST and RPC?

**Answer:**
| Feature | REST | RPC |
|---------|------|-----|
| Style | Resource-oriented | Action-oriented |
| Protocol | HTTP | Custom or HTTP |
| Data Format | JSON, XML | Protobuf, JSON |
| Example | GET /files/123 | getFile(123) |
| Statefulness | Stateless | Can be stateful |

We chose REST because it's simpler, standardized, and easy to test.

---

## 30. How is your system different from a traditional backup system?

**Answer:**
| Feature | Backup System | Our Distributed Storage |
|---------|--------------|------------------------|
| Data Location | Copied to backup server | Split and distributed across nodes |
| Access | Restore from backup | Direct access from any replica |
| Speed | Full restore needed | Parallel retrieval from multiple nodes |
| Scaling | Limited by backup server | Horizontally scalable |
| Availability | Only during restore | Real-time availability |
| Goal | Disaster recovery | High availability + scalability |

---

## 31. What is data deduplication?

**Answer:** Data deduplication is a technique to eliminate redundant copies of data. If two users upload the same file, the system stores only one copy and maintains references.

Our system does NOT implement deduplication (each upload creates new chunks), but it could be added by computing file hashes and checking for duplicates before storing.

---

## 32. What tools/libraries did you use?

**Answer:**
| Tool/Library | Purpose |
|---|---|
| **Python 3** | Programming language |
| **Flask** | Web framework for REST APIs |
| **SQLite** | Metadata database |
| **bcrypt** | Password hashing |
| **requests** | HTTP client for inter-node communication |
| **threading** | Background health monitoring |
| **uuid** | Generating unique file/chunk IDs |
| **HTML/CSS/JS** | Frontend UI |
