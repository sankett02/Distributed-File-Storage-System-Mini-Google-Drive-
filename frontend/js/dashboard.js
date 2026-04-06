/**
 * Dashboard Module (Frontend)
 * ----------------------------
 * Handles all dashboard functionality:
 *   - File upload with drag & drop
 *   - File listing, download, and deletion
 *   - Node status monitoring with live refresh
 *   - Toast notifications
 *   - Stats display
 */

const API_BASE = "http://localhost:5000";

// Auto-refresh interval for node status (ms)
const REFRESH_INTERVAL = 10000; // 10 seconds

// ══════════════════════════════════════════════
// PAGE INITIALIZATION
// ══════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    checkDashboardAuth();
    setupDragAndDrop();
});

/**
 * Check if user is authenticated. Redirect to login if not.
 */
async function checkDashboardAuth() {
    try {
        const response = await fetch(`${API_BASE}/api/me`, {
            credentials: "include"
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById("usernameDisplay").textContent = `👤 ${data.username}`;
            // Load initial data
            loadFiles();
            loadNodeStatus();
            // Start auto-refresh
            setInterval(loadNodeStatus, REFRESH_INTERVAL);
        } else {
            window.location.href = "/";
        }
    } catch (err) {
        showToast("Cannot connect to server", "error");
        console.error("Auth check failed:", err);
    }
}

// ══════════════════════════════════════════════
// FILE UPLOAD
// ══════════════════════════════════════════════

/**
 * Setup drag and drop event listeners on the upload zone.
 */
function setupDragAndDrop() {
    const zone = document.getElementById("uploadZone");

    zone.addEventListener("dragover", (e) => {
        e.preventDefault();
        zone.classList.add("dragover");
    });

    zone.addEventListener("dragleave", () => {
        zone.classList.remove("dragover");
    });

    zone.addEventListener("drop", (e) => {
        e.preventDefault();
        zone.classList.remove("dragover");
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    });
}

/**
 * Handle file selection via the file input.
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        uploadFile(file);
    }
}

/**
 * Upload a file to the master node.
 * Shows progress bar during upload.
 *
 * @param {File} file - The file to upload
 */
async function uploadFile(file) {
    // Validate file size (50 MB limit)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast("File too large. Maximum size is 50 MB", "error");
        return;
    }

    // Show progress UI
    const progressDiv = document.getElementById("uploadProgress");
    const progressBar = document.getElementById("progressBar");
    const progressText = document.getElementById("progressText");
    progressDiv.style.display = "block";
    progressBar.style.width = "0%";
    progressText.textContent = `Uploading ${file.name}...`;

    // Create FormData with the file
    const formData = new FormData();
    formData.append("file", file);

    try {
        // Use XMLHttpRequest for upload progress tracking
        const xhr = new XMLHttpRequest();

        // Track upload progress
        xhr.upload.addEventListener("progress", (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = `${percent}%`;
                progressText.textContent = `Uploading ${file.name}... ${percent}%`;
            }
        });

        // Wrap XHR in a promise
        const uploadPromise = new Promise((resolve, reject) => {
            xhr.onload = () => {
                if (xhr.status === 200) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    try {
                        const errData = JSON.parse(xhr.responseText);
                        reject(new Error(errData.error || "Upload failed"));
                    } catch {
                        reject(new Error("Upload failed"));
                    }
                }
            };
            xhr.onerror = () => reject(new Error("Network error"));
        });

        xhr.open("POST", `${API_BASE}/api/upload`);
        xhr.withCredentials = true;
        xhr.send(formData);

        const result = await uploadPromise;

        // Upload successful
        progressBar.style.width = "100%";
        progressText.textContent = `✅ ${file.name} uploaded successfully! (${result.chunks} chunks)`;
        showToast(`File "${file.name}" uploaded — split into ${result.chunks} chunks, replicated ${result.replication_factor}x`, "success");

        // Refresh file list and node status
        loadFiles();
        loadNodeStatus();

        // Reset file input
        document.getElementById("fileInput").value = "";

        // Hide progress after a delay
        setTimeout(() => {
            progressDiv.style.display = "none";
        }, 3000);

    } catch (err) {
        progressBar.style.width = "0%";
        progressText.textContent = `❌ Upload failed: ${err.message}`;
        showToast(`Upload failed: ${err.message}`, "error");
    }
}

// ══════════════════════════════════════════════
// FILE LISTING
// ══════════════════════════════════════════════

/**
 * Load and display all files for the current user.
 */
async function loadFiles() {
    try {
        const response = await fetch(`${API_BASE}/api/files`, {
            credentials: "include"
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = "/";
                return;
            }
            throw new Error("Failed to load files");
        }

        const data = await response.json();
        renderFileTable(data.files);
        updateStats(data.files);

    } catch (err) {
        console.error("Error loading files:", err);
    }
}

/**
 * Render the file table with data.
 *
 * @param {Array} files - Array of file metadata objects
 */
function renderFileTable(files) {
    const tbody = document.getElementById("filesTableBody");

    if (!files || files.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5">
                    <div class="empty-state">
                        <div class="empty-icon">📭</div>
                        <p>No files uploaded yet. Upload your first file above!</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = files.map(file => {
        const icon = getFileIcon(file.original_name);
        const date = new Date(file.created_at).toLocaleDateString("en-IN", {
            day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"
        });

        return `
            <tr>
                <td>
                    <span class="file-name">
                        <span class="file-icon">${icon}</span>
                        ${escapeHtml(file.original_name)}
                    </span>
                </td>
                <td>${file.size_display}</td>
                <td>${file.chunk_count}</td>
                <td>${date}</td>
                <td>
                    <div class="file-actions">
                        <button class="btn-download" onclick="downloadFile('${file.file_id}', '${escapeHtml(file.original_name)}')">
                            ⬇ Download
                        </button>
                        <button class="btn-delete" onclick="deleteFile('${file.file_id}', '${escapeHtml(file.original_name)}')">
                            🗑 Delete
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

/**
 * Get an emoji icon based on file extension.
 */
function getFileIcon(filename) {
    const ext = filename.split(".").pop().toLowerCase();
    const icons = {
        pdf: "📄", doc: "📝", docx: "📝", txt: "📃",
        jpg: "🖼️", jpeg: "🖼️", png: "🖼️", gif: "🖼️", svg: "🖼️",
        mp4: "🎬", avi: "🎬", mov: "🎬", mkv: "🎬",
        mp3: "🎵", wav: "🎵", flac: "🎵",
        zip: "📦", rar: "📦", "7z": "📦", tar: "📦",
        py: "🐍", js: "💛", html: "🌐", css: "🎨",
        java: "☕", cpp: "⚡", c: "⚡",
        xlsx: "📊", csv: "📊", xls: "📊",
        pptx: "📽️", ppt: "📽️",
        exe: "⚙️", msi: "⚙️",
    };
    return icons[ext] || "📄";
}

// ══════════════════════════════════════════════
// FILE DOWNLOAD
// ══════════════════════════════════════════════

/**
 * Download a file from the distributed storage.
 * The master node assembles chunks on the fly.
 */
async function downloadFile(fileId, filename) {
    showToast(`Downloading "${filename}"...`, "info");

    try {
        const response = await fetch(`${API_BASE}/api/download/${fileId}`, {
            credentials: "include"
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || "Download failed");
        }

        // Create a download link from the response blob
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        showToast(`"${filename}" downloaded successfully`, "success");

    } catch (err) {
        showToast(`Download failed: ${err.message}`, "error");
    }
}

// ══════════════════════════════════════════════
// FILE DELETE
// ══════════════════════════════════════════════

/**
 * Delete a file from the distributed storage.
 * Removes chunks from all storage nodes.
 */
async function deleteFile(fileId, filename) {
    // Confirm deletion
    if (!confirm(`Are you sure you want to delete "${filename}"?\nThis will remove all chunks from all storage nodes.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/delete/${fileId}`, {
            method: "DELETE",
            credentials: "include"
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || "Delete failed");
        }

        showToast(`"${filename}" deleted successfully`, "success");
        loadFiles();
        loadNodeStatus();

    } catch (err) {
        showToast(`Delete failed: ${err.message}`, "error");
    }
}

// ══════════════════════════════════════════════
// NODE STATUS
// ══════════════════════════════════════════════

/**
 * Load and display the status of all storage nodes.
 * Called on page load and every REFRESH_INTERVAL ms.
 */
async function loadNodeStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/nodes`, {
            credentials: "include"
        });

        if (!response.ok) throw new Error("Failed to load node status");

        const data = await response.json();
        renderNodeCards(data.nodes);

        // Update stats
        document.getElementById("statNodes").textContent =
            `${data.healthy_count}/${data.total_count}`;

    } catch (err) {
        console.error("Error loading node status:", err);
    }
}

/**
 * Render node status cards.
 *
 * @param {Array} nodes - Array of node status objects
 */
function renderNodeCards(nodes) {
    const grid = document.getElementById("nodesGrid");

    grid.innerHTML = nodes.map(node => {
        const statusClass = node.status === "healthy" ? "healthy" : "dead";
        const lastCheck = node.last_check
            ? new Date(node.last_check).toLocaleTimeString()
            : "Never";

        return `
            <div class="node-card ${statusClass}">
                <div class="node-header">
                    <span class="node-name">🖥️ ${node.node_id.toUpperCase()}</span>
                    <span class="node-status-badge ${statusClass}">
                        ${node.status === "healthy" ? "● Online" : "● Offline"}
                    </span>
                </div>
                <div class="node-meta">
                    <span>📡 Port: ${node.port}</span>
                    <span>📦 Chunks: ${node.chunk_count || 0}</span>
                    <span>💾 Usage: ${node.disk_usage_mb || 0} MB</span>
                    <span>🕐 Last Check: ${lastCheck}</span>
                </div>
                <button class="node-toggle"
                        onclick="toggleNode('${node.node_id}')">
                    ${node.status === "healthy"
                        ? "⚡ Simulate Failure"
                        : "🔄 Restore Node"}
                </button>
            </div>
        `;
    }).join("");
}

/**
 * Toggle a node on/off (simulate failure / restore).
 * Used for demonstrating fault tolerance.
 */
async function toggleNode(nodeId) {
    try {
        const response = await fetch(`${API_BASE}/api/nodes/${nodeId}/toggle`, {
            method: "POST",
            credentials: "include"
        });

        if (!response.ok) throw new Error("Failed to toggle node");

        const data = await response.json();

        if (data.status === "dead") {
            showToast(`Node ${nodeId} is now OFFLINE (simulated failure)`, "error");
        } else {
            showToast(`Node ${nodeId} is back ONLINE`, "success");
        }

        // Refresh node status
        loadNodeStatus();

    } catch (err) {
        showToast(`Failed to toggle node: ${err.message}`, "error");
    }
}

// ══════════════════════════════════════════════
// STATS
// ══════════════════════════════════════════════

/**
 * Update the stats cards based on file data.
 */
function updateStats(files) {
    // Total files
    document.getElementById("statFiles").textContent = files.length;

    // Total storage
    const totalBytes = files.reduce((sum, f) => sum + f.file_size, 0);
    document.getElementById("statStorage").textContent = formatBytes(totalBytes);
}

/**
 * Format bytes to human-readable string.
 */
function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

// ══════════════════════════════════════════════
// TOAST NOTIFICATIONS
// ══════════════════════════════════════════════

/**
 * Show a toast notification.
 *
 * @param {string} message - The notification message
 * @param {string} type - "success", "error", or "info"
 */
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    // Remove toast after animation
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// ══════════════════════════════════════════════
// LOGOUT
// ══════════════════════════════════════════════

async function handleLogout() {
    try {
        await fetch(`${API_BASE}/api/logout`, {
            method: "POST",
            credentials: "include"
        });
    } catch (err) {
        // Ignore errors on logout
    }
    window.location.href = "/";
}

// ══════════════════════════════════════════════
// UTILITIES
// ══════════════════════════════════════════════

/**
 * Escape HTML to prevent XSS when inserting user content.
 */
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
