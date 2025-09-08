@echo off
title Smart File Search - Windows Network Folder Edition

echo ============================================================
echo Smart File Search - Windows Network Folder Edition
echo ============================================================
echo.
echo This system is optimized for searching Windows network folders
echo with simple search functionality prioritized.
echo.

:: Check Python
echo [1/3] Checking Python installation...
where python >nul 2>nul
if errorlevel 1 (
    echo ❌ Error: Python not found. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python found

:: Check Node.js
echo [2/3] Checking Node.js installation...
where node >nul 2>nul
if errorlevel 1 (
    echo ❌ Error: Node.js not found. Please install Node.js first.
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)
echo ✅ Node.js found

:: Setup virtual environment if needed
echo [3/3] Setting up Python environment...
if not exist "%~dp0..\venv" (
    echo Creating virtual environment...
    cd /d "%~dp0.."
    python -m venv venv
)

:: Activate virtual environment and install dependencies
echo Activating virtual environment...
call "%~dp0..\venv\Scripts\activate.bat"

:: Install Python dependencies
echo Installing Python dependencies...
cd /d "%~dp0.."
pip install -r requirements.txt

echo.
echo ============================================================
echo Starting Services...
echo ============================================================
echo.

:: Start backend in new window
echo Starting backend server...
start "Smart File Search Backend" cmd /k ""%~dp0start_backend.bat""

:: Wait a moment for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend in new window
echo Starting frontend server...
start "Smart File Search Frontend" cmd /k ""%~dp0start_frontend.bat""

echo.
echo ============================================================
echo 🚀 Smart File Search is starting up!
echo ============================================================
echo.
echo Services starting:
echo   - Backend API: http://localhost:8000
echo   - Frontend UI: http://localhost:3000
echo.
echo Open your browser to: http://localhost:3000
echo.
echo To get started:
echo   1. Enter a Windows network path (e.g., \\server\share)
echo   2. Wait for validation and indexing
echo   3. Start searching your files!
echo.
echo Press any key to close this window...
pause >nul
