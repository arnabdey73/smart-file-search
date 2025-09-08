@echo off
REM Index sample data for testing

echo Indexing sample data...
echo.

set PYTHONPATH=%CD%
set DB_PATH=%CD%\data\file_index.sqlite3

REM Run indexing
venv\Scripts\python.exe -m search_agent.cli index "%CD%\sample_data" --priority normal

echo.
echo Indexing complete! You can now search the sample data.
pause
