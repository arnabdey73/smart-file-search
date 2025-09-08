@echo off
REM Search test script

set PYTHONPATH=%CD%
set DB_PATH=%CD%\data\file_index.sqlite3

echo Testing search functionality...
echo.

if "%1"=="" (
    echo Usage: search_test.bat "your search query"
    echo Example: search_test.bat "python programming"
    pause
    exit /b
)

echo Searching for: %1
echo.

venv\Scripts\python.exe -m search_agent.cli search %1

echo.
pause
