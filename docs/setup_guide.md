# Setup Guide — Distributed File Storage System

## Prerequisites

1. **Python 3.8+** installed ([Download Python](https://www.python.org/downloads/))
2. **pip** (Python package manager, comes with Python)
3. **Web browser** (Chrome, Firefox, or Edge recommended)

### Verify Python Installation
Open Command Prompt and run:
```bash
python --version
```
Expected output: `Python 3.x.x`

---

## Step 1: Download / Clone the Project

Place the project folder at your desired location. The folder structure should be:
```
DC mini/
├── master/
├── storage_node/
├── frontend/
├── docs/
├── requirements.txt
├── start_system.bat
└── README.md
```

---

## Step 2: Install Python Dependencies

Open Command Prompt, navigate to the project folder, and run:

```bash
cd "path\to\DC mini"
pip install -r requirements.txt
```

This installs:
- **Flask** — Web framework
- **flask-cors** — Cross-origin support
- **bcrypt** — Password hashing
- **requests** — HTTP client for inter-node communication

---

## Step 3: Start the System

### Option A: Using the Batch Script (Recommended for Windows)

Simply double-click `start_system.bat` or run:
```bash
start_system.bat
```

This opens 4 terminal windows:
- Storage Node 1 (Port 5001)
- Storage Node 2 (Port 5002)
- Storage Node 3 (Port 5003)
- Master Node (Port 5000)

### Option B: Manual Start (Any OS)

Open **4 separate terminal windows** and run:

**Terminal 1 — Storage Node 1:**
```bash
cd "DC mini/storage_node"
python node.py --port 5001 --node-id node1
```

**Terminal 2 — Storage Node 2:**
```bash
cd "DC mini/storage_node"
python node.py --port 5002 --node-id node2
```

**Terminal 3 — Storage Node 3:**
```bash
cd "DC mini/storage_node"
python node.py --port 5003 --node-id node3
```

**Terminal 4 — Master Node:**
```bash
cd "DC mini/master"
python app.py
```

---

## Step 4: Open the Application

Open your browser and go to:

🔗 **http://localhost:5000**

You should see the CloudVault login page.

---

## Step 5: Test the System

### 5.1 Create an Account
1. Click the **"Sign Up"** tab
2. Enter a username (min 3 characters)
3. Enter a password (min 4 characters)
4. Click **"Create Account"**

### 5.2 Login
1. Switch to the **"Login"** tab
2. Enter your credentials
3. Click **"Login"**
4. You'll be redirected to the dashboard

### 5.3 Upload a File
1. Click the upload area or drag & drop a file
2. Watch the progress bar
3. File appears in the files table

### 5.4 Check Node Status
- All 3 nodes should show as **"Online"** (green)
- Chunk counts should update after uploading files

### 5.5 Test Fault Tolerance
1. Click **"Simulate Failure"** on Node 1
2. Node 1 turns **red (Offline)**
3. Try downloading a file — it should work using replicas from other nodes!
4. Click **"Restore Node"** to bring it back

### 5.6 Download a File
1. Click **"Download"** button next to any file
2. File is reconstructed from chunks and downloaded

### 5.7 Delete a File
1. Click **"Delete"** button
2. Confirm in the dialog
3. File and all its chunks are removed

---

## Step 6: Stop the System

Close all 4 terminal windows, or press `Ctrl+C` in each terminal.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Module not found" error** | Run `pip install -r requirements.txt` |
| **Port already in use** | Kill the process using that port: `netstat -ano \| findstr :5000` then `taskkill /PID <pid> /F` |
| **"Cannot connect to server"** | Make sure the master node (port 5000) is running |
| **Nodes showing as "Offline"** | Make sure all 3 storage node terminals are running |
| **Upload fails** | Check that at least 1 storage node is healthy |

---

## Verifying the System

### Check Metadata (SQLite)
You can inspect the database using any SQLite viewer or Python:
```python
import sqlite3
conn = sqlite3.connect("master/database.db")
cursor = conn.cursor()

# List all files
cursor.execute("SELECT * FROM files")
print(cursor.fetchall())

# List chunk locations
cursor.execute("SELECT * FROM chunk_locations")
print(cursor.fetchall())

conn.close()
```

### Check Storage Directories
After uploading files, you can verify chunks on disk:
```
storage_node/storage/node1/   ← Chunks stored on Node 1
storage_node/storage/node2/   ← Chunks stored on Node 2
storage_node/storage/node3/   ← Chunks stored on Node 3
```

### Check Logs
Master node logs are stored in:
```
master/logs/master.log
```
