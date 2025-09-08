@echo off
REM Smart File Search - Native Windows Runner
REM Runs all services without Docker

echo Starting Smart File Search System (Native Windows)
echo ================================================

REM Create data directory
if not exist "data" mkdir data
if not exist "logs" mkdir logs

REM Set environment variables
set PYTHONPATH=%CD%
set DB_PATH=%CD%\data\file_index.sqlite3
set MCP_PORT=9000
set UI_BACKEND_PORT=8081

echo.
echo [1/3] Starting MCP Server on port %MCP_PORT%...
start "MCP Server" cmd /k "venv\Scripts\python.exe -m mcp_server.server"

REM Wait a moment for MCP server to start
timeout /t 3 /nobreak >nul

echo [2/3] Starting UI Backend on port %UI_BACKEND_PORT%...
start "UI Backend" cmd /k "cd ui\backend && ..\..\venv\Scripts\python.exe api_network_main.py"

echo [3/3] Services starting...
echo.
echo ================================================
echo Smart File Search is starting up!
echo.
echo Services:
echo - MCP Server:  http://localhost:%MCP_PORT%
echo - API Backend: http://localhost:%UI_BACKEND_PORT%
echo - Health:      http://localhost:%UI_BACKEND_PORT%/healthz
echo.
echo To stop services, close the command windows.
echo ================================================

pause
