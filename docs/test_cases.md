# Test Cases — Distributed File Storage System

## Test Environment Setup
- Master Node running on port 5000
- Storage Nodes running on ports 5001, 5002, 5003
- All nodes on localhost

---

## TC-01: User Registration (Signup)

| Field | Details |
|-------|---------|
| **Test ID** | TC-01 |
| **Description** | Register a new user |
| **Precondition** | System is running, username does not exist |
| **Steps** | 1. Open http://localhost:5000 <br> 2. Click "Sign Up" tab <br> 3. Enter username: "testuser" <br> 4. Enter password: "test1234" <br> 5. Confirm password: "test1234" <br> 6. Click "Create Account" |
| **Expected Result** | Success message: "Account created! You can now login." |
| **Status** | ✅ |

---

## TC-02: Duplicate User Registration

| Field | Details |
|-------|---------|
| **Test ID** | TC-02 |
| **Description** | Try to register with an existing username |
| **Precondition** | User "testuser" already exists |
| **Steps** | 1. Try to sign up with username "testuser" again |
| **Expected Result** | Error message: "Username already exists" |
| **Status** | ✅ |

---

## TC-03: User Login

| Field | Details |
|-------|---------|
| **Test ID** | TC-03 |
| **Description** | Login with valid credentials |
| **Precondition** | User "testuser" is registered |
| **Steps** | 1. Enter username: "testuser" <br> 2. Enter password: "test1234" <br> 3. Click "Login" |
| **Expected Result** | Redirected to dashboard, username displayed in navbar |
| **Status** | ✅ |

---

## TC-04: Invalid Login

| Field | Details |
|-------|---------|
| **Test ID** | TC-04 |
| **Description** | Login with wrong password |
| **Precondition** | User "testuser" exists |
| **Steps** | 1. Enter username: "testuser" <br> 2. Enter password: "wrongpassword" <br> 3. Click "Login" |
| **Expected Result** | Error message: "Invalid username or password" |
| **Status** | ✅ |

---

## TC-05: File Upload (Small File)

| Field | Details |
|-------|---------|
| **Test ID** | TC-05 |
| **Description** | Upload a small text file |
| **Precondition** | User is logged in, all nodes healthy |
| **Steps** | 1. Click upload area or drag file <br> 2. Select a file (e.g., test.txt, 100 bytes) <br> 3. Wait for upload to complete |
| **Expected Result** | Success toast: "File uploaded - split into 1 chunk, replicated 2x". File appears in table. |
| **Status** | ✅ |

---

## TC-06: File Upload (Large File with Multiple Chunks)

| Field | Details |
|-------|---------|
| **Test ID** | TC-06 |
| **Description** | Upload a file larger than chunk size (>256 KB) |
| **Precondition** | User is logged in, all nodes healthy |
| **Steps** | 1. Upload a file of ~1 MB |
| **Expected Result** | File split into 4 chunks. Chunks distributed across nodes. File appears in table with chunk count = 4. |
| **Status** | ✅ |

---

## TC-07: File Download

| Field | Details |
|-------|---------|
| **Test ID** | TC-07 |
| **Description** | Download a previously uploaded file |
| **Precondition** | File has been uploaded |
| **Steps** | 1. Click "Download" button next to the file |
| **Expected Result** | File downloads. Content matches the original uploaded file exactly. |
| **Status** | ✅ |

---

## TC-08: File Delete

| Field | Details |
|-------|---------|
| **Test ID** | TC-08 |
| **Description** | Delete a file from storage |
| **Precondition** | File has been uploaded |
| **Steps** | 1. Click "Delete" button <br> 2. Confirm deletion in dialog |
| **Expected Result** | File removed from table. Chunks deleted from all storage nodes. |
| **Status** | ✅ |

---

## TC-09: Node Health Check

| Field | Details |
|-------|---------|
| **Test ID** | TC-09 |
| **Description** | Verify node status display |
| **Precondition** | All nodes running |
| **Steps** | 1. Check the "Storage Nodes" section on dashboard |
| **Expected Result** | All 3 nodes show "Online" (green). Chunk counts and disk usage displayed. |
| **Status** | ✅ |

---

## TC-10: Simulate Node Failure

| Field | Details |
|-------|---------|
| **Test ID** | TC-10 |
| **Description** | Toggle a node off to simulate failure |
| **Precondition** | All nodes healthy |
| **Steps** | 1. Click "Simulate Failure" on Node 1 |
| **Expected Result** | Node 1 shows "Offline" (red). Healthy nodes count decreases to 2/3. |
| **Status** | ✅ |

---

## TC-11: Fault-Tolerant Download

| Field | Details |
|-------|---------|
| **Test ID** | TC-11 |
| **Description** | Download a file when one node is down |
| **Precondition** | File uploaded to nodes 1 & 2. Node 1 is toggled OFF. |
| **Steps** | 1. Disable Node 1 <br> 2. Click Download on the file |
| **Expected Result** | File downloads successfully using replicas from Node 2. Master log shows "Skipping node1, trying replica..." |
| **Status** | ✅ |

---

## TC-12: File Upload with Insufficient Nodes

| Field | Details |
|-------|---------|
| **Test ID** | TC-12 |
| **Description** | Upload when all nodes are down |
| **Precondition** | All 3 nodes are toggled OFF |
| **Steps** | 1. Try to upload a file |
| **Expected Result** | Error message: "No storage nodes available. System is down." |
| **Status** | ✅ |

---

## TC-13: Restore Node After Failure

| Field | Details |
|-------|---------|
| **Test ID** | TC-13 |
| **Description** | Re-enable a previously disabled node |
| **Precondition** | Node 1 is toggled OFF |
| **Steps** | 1. Click "Restore Node" on Node 1 |
| **Expected Result** | Node 1 shows "Online" (green) again. Healthy count returns to 3/3. |
| **Status** | ✅ |

---

## TC-14: Unauthorized File Access

| Field | Details |
|-------|---------|
| **Test ID** | TC-14 |
| **Description** | Try API call without login |
| **Precondition** | User is not logged in |
| **Steps** | 1. Open http://localhost:5000/api/files directly |
| **Expected Result** | 401 error: "Authentication required. Please login." |
| **Status** | ✅ |

---

## TC-15: File Integrity Check

| Field | Details |
|-------|---------|
| **Test ID** | TC-15 |
| **Description** | Verify uploaded and downloaded file are identical |
| **Precondition** | A binary file (e.g., image) has been uploaded |
| **Steps** | 1. Upload an image file <br> 2. Download it <br> 3. Compare file sizes and checksums |
| **Expected Result** | Downloaded file is byte-for-byte identical to the original |
| **Status** | ✅ |
