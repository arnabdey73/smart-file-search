@echo off
echo Starting Smart File Search Frontend...

:: Navigate to frontend directory
cd /d "%~dp0..\ui\frontend"

:: Check if Node.js is available
where node >nul 2>nul
if errorlevel 1 (
    echo Error: Node.js not found. Please install Node.js first.
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)

:: Install dependencies if needed
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

:: Start the development server
echo Starting Vite development server...
npm run dev

pause
