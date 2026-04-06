/**
 * Authentication Module (Frontend)
 * ---------------------------------
 * Handles login and signup form submissions.
 * Communicates with the master node's auth API.
 */

const API_BASE = ""; // Relative path to support localhost, 127.0.0.1, or local IP

// ──────────────────────────────────────────────
// Tab Switching (Login ↔ Signup)
// ──────────────────────────────────────────────

function switchTab(tab) {
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");
    const loginTab = document.getElementById("loginTab");
    const signupTab = document.getElementById("signupTab");

    // Hide alerts
    hideAlerts();

    if (tab === "login") {
        loginForm.style.display = "block";
        signupForm.style.display = "none";
        loginTab.classList.add("active");
        signupTab.classList.remove("active");
    } else {
        loginForm.style.display = "none";
        signupForm.style.display = "block";
        loginTab.classList.remove("active");
        signupTab.classList.add("active");
    }
}

// ──────────────────────────────────────────────
// Alert Display Helpers
// ──────────────────────────────────────────────

function showError(message) {
    const alert = document.getElementById("authAlert");
    alert.textContent = message;
    alert.style.display = "block";
    document.getElementById("authSuccess").style.display = "none";
}

function showSuccess(message) {
    const alert = document.getElementById("authSuccess");
    alert.textContent = message;
    alert.style.display = "block";
    document.getElementById("authAlert").style.display = "none";
}

function hideAlerts() {
    document.getElementById("authAlert").style.display = "none";
    document.getElementById("authSuccess").style.display = "none";
}

// ──────────────────────────────────────────────
// Login Handler
// ──────────────────────────────────────────────

async function handleLogin(event) {
    event.preventDefault();
    hideAlerts();

    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value.trim();

    if (!username || !password) {
        showError("Please fill in all fields");
        return;
    }

    const btn = document.getElementById("loginBtn");
    btn.innerHTML = '<span class="loading-spinner"></span> Logging in...';
    btn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/api/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",    // Important: send session cookies
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess("Login successful! Redirecting...");
            // Redirect to dashboard after brief delay
            setTimeout(() => {
                window.location.href = "/dashboard";
            }, 800);
        } else {
            showError(data.error || "Login failed");
        }
    } catch (err) {
        showError("Cannot connect to server. Make sure the master node is running.");
        console.error("Login error:", err);
    } finally {
        btn.innerHTML = "Login";
        btn.disabled = false;
    }
}

// ──────────────────────────────────────────────
// Signup Handler
// ──────────────────────────────────────────────

async function handleSignup(event) {
    event.preventDefault();
    hideAlerts();

    const username = document.getElementById("signupUsername").value.trim();
    const password = document.getElementById("signupPassword").value.trim();
    const confirm = document.getElementById("confirmPassword").value.trim();

    // Client-side validation
    if (!username || !password || !confirm) {
        showError("Please fill in all fields");
        return;
    }

    if (username.length < 3) {
        showError("Username must be at least 3 characters");
        return;
    }

    if (password.length < 4) {
        showError("Password must be at least 4 characters");
        return;
    }

    if (password !== confirm) {
        showError("Passwords do not match");
        return;
    }

    const btn = document.getElementById("signupBtn");
    btn.innerHTML = '<span class="loading-spinner"></span> Creating account...';
    btn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/api/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess("Account created! You can now login.");
            // Switch to login tab
            setTimeout(() => {
                switchTab("login");
                document.getElementById("loginUsername").value = username;
            }, 1500);
        } else {
            showError(data.error || "Signup failed");
        }
    } catch (err) {
        showError("Cannot connect to server. Make sure the master node is running.");
        console.error("Signup error:", err);
    } finally {
        btn.innerHTML = "Create Account";
        btn.disabled = false;
    }
}

// ──────────────────────────────────────────────
// Check if already logged in on page load
// ──────────────────────────────────────────────

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/api/me`, {
            credentials: "include"
        });
        if (response.ok) {
            // Already logged in, redirect to dashboard
            window.location.href = "/dashboard";
        }
    } catch (err) {
        // Not logged in or server not running, stay on login page
    }
}

// Run on page load
checkAuth();
