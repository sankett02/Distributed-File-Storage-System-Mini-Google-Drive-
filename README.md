# CloudVault — Distributed File Storage System

> **Mini Google Drive** built using distributed computing concepts  
> Mumbai University • B.E. Computer Engineering • Semester 8 • Distributed Computing

---

## 🎯 Project Overview

CloudVault is a **Distributed File Storage System** that demonstrates core distributed computing concepts. Files uploaded by users are split into chunks, distributed across multiple storage nodes, and replicated for fault tolerance — similar to how Google Drive and HDFS work internally.

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **File Chunking** | Files are split into 256 KB chunks for distributed storage |
| **Replication** | Each chunk is stored on 2 nodes (configurable) |
| **Fault Tolerance** | Files remain accessible even when a node fails |
| **Load Balancing** | Round-robin distribution of chunks across nodes |
| **Health Monitoring** | Background thread checks node health every 10 seconds |
| **User Auth** | Signup/login with bcrypt password hashing |
| **Node Simulation** | Toggle nodes on/off from the dashboard to test fault tolerance |
| **Logging** | Structured logs for all operations |

## 🏗️ Architecture

```
              ┌──────────────┐
              │   Frontend   │
              │  (Browser)   │
              └──────┬───────┘
                     │ REST API
              ┌──────▼───────┐
              │ Master Node  │  ← Port 5000
              │ (Coordinator)│
              └──┬───┬───┬───┘
                 │   │   │
          ┌──────┘   │   └──────┐
          │          │          │
    ┌─────▼────┐ ┌──▼──────┐ ┌─▼────────┐
    │  Node 1  │ │  Node 2 │ │  Node 3  │
    │ Port 5001│ │ Port 5002│ │ Port 5003│
    └──────────┘ └─────────┘ └──────────┘
```

## 🛠️ Tech Stack

- **Backend**: Python 3.x with Flask
- **Database**: SQLite (metadata)
- **Frontend**: HTML, CSS, JavaScript
- **Auth**: bcrypt password hashing + Flask sessions
- **Communication**: REST APIs

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ installed
- pip (Python package manager)

### Step 1: Install Dependencies
```bash
cd "DC mini"
pip install -r requirements.txt
```

### Step 2: Start the System
**Windows (recommended):**
```bash
start_system.bat
```

**Manual start (any OS):**
```bash
# Terminal 1 — Storage Node 1
cd storage_node
python node.py --port 5001 --node-id node1

# Terminal 2 — Storage Node 2
cd storage_node
python node.py --port 5002 --node-id node2

# Terminal 3 — Storage Node 3
cd storage_node
python node.py --port 5003 --node-id node3

# Terminal 4 — Master Node
cd master
python app.py
```

### Step 3: Open the App
Go to **http://localhost:5000** in your browser.

## 📂 Folder Structure

```
DC mini/
├── master/                 # Coordinator node
│   ├── app.py             # Main Flask app
│   ├── config.py          # Configuration
│   ├── auth.py            # Authentication
│   ├── file_manager.py    # Upload/download/delete logic
│   ├── metadata.py        # SQLite database operations
│   ├── health_monitor.py  # Node health checking
│   ├── load_balancer.py   # Round-robin balancing
│   ├── replicator.py      # Chunk replication
│   └── logger_config.py   # Logging setup
│
├── storage_node/           # Storage node template
│   ├── node.py            # Storage node server
│   └── config.py          # Node configuration
│
├── frontend/               # Web UI
│   ├── index.html         # Login page
│   ├── dashboard.html     # Dashboard
│   ├── css/style.css      # Styles
│   └── js/                # JavaScript modules
│
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
├── start_system.bat        # Windows startup script
└── README.md              # This file
```

## 📝 Distributed Concepts Implemented

1. **Replication** — Each chunk stored on multiple nodes
2. **Fault Tolerance** — System works even when nodes fail
3. **Load Balancing** — Round-robin chunk distribution
4. **Consistency** — Metadata in centralized SQLite database
5. **Distributed Communication** — REST APIs between nodes

## 👨‍🎓 Academic Info

- **University**: Mumbai University
- **Branch**: Computer Engineering
- **Semester**: 8
- **Subject**: Distributed Computing
- **Project Type**: Mini Project

---

*Built with ❤️ for Distributed Computing*
