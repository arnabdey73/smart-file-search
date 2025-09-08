@echo off
echo Starting Smart File Search Backend...

:: Navigate to backend directory
cd /d "%~dp0..\ui\backend"

:: Activate virtual environment if it exists
if exist "%~dp0..\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "%~dp0..\venv\Scripts\activate.bat"
)

:: Start the network-optimized FastAPI backend
echo Starting FastAPI server for Windows network folders...
python api_network_main.py

pause
