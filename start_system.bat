@echo off
REM ═══════════════════════════════════════════════════════════
REM  DISTRIBUTED FILE STORAGE SYSTEM — Startup Script
REM  Starts all nodes: 3 Storage Nodes + 1 Master Node
REM ═══════════════════════════════════════════════════════════

echo.
echo  ╔════════════════════════════════════════════════════╗
echo  ║   CloudVault — Distributed File Storage System     ║
echo  ║   Starting all nodes...                            ║
echo  ╚════════════════════════════════════════════════════╝
echo.

REM Get the directory where this script is located
set BASE_DIR=%~dp0

REM ─── Start Storage Node 1 (Port 5001) ───
echo [*] Starting Storage Node 1 on port 5001...
start "Storage Node 1" cmd /k "cd /d %BASE_DIR%storage_node && python node.py --port 5001 --node-id node1"
timeout /t 1 /nobreak >nul

REM ─── Start Storage Node 2 (Port 5002) ───
echo [*] Starting Storage Node 2 on port 5002...
start "Storage Node 2" cmd /k "cd /d %BASE_DIR%storage_node && python node.py --port 5002 --node-id node2"
timeout /t 1 /nobreak >nul

REM ─── Start Storage Node 3 (Port 5003) ───
echo [*] Starting Storage Node 3 on port 5003...
start "Storage Node 3" cmd /k "cd /d %BASE_DIR%storage_node && python node.py --port 5003 --node-id node3"
timeout /t 2 /nobreak >nul

REM ─── Start Master Node (Port 5000) ───
echo [*] Starting Master Node on port 5000...
start "Master Node" cmd /k "cd /d %BASE_DIR%master && python app.py"
timeout /t 2 /nobreak >nul

echo.
echo  ╔════════════════════════════════════════════════════╗
echo  ║   All nodes started successfully!                  ║
echo  ║                                                    ║
echo  ║   Master Node:    http://localhost:5000             ║
echo  ║   Storage Node 1: http://localhost:5001             ║
echo  ║   Storage Node 2: http://localhost:5002             ║
echo  ║   Storage Node 3: http://localhost:5003             ║
echo  ║                                                    ║
echo  ║   Open http://localhost:5000 in your browser        ║
echo  ╚════════════════════════════════════════════════════╝
echo.
pause
