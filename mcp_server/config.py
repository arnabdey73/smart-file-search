"""
Configuration module for MCP server.
Handles server settings and environment variables.
"""

import os
from typing import Dict, Any

def get_config() -> Dict[str, Any]:
    """
    Get configuration settings for the MCP server.
    
    Returns:
        Dictionary containing configuration settings
    """
    return {
        "server_name": os.getenv("MCP_SERVER_NAME", "smart-file-search"),
        "host": os.getenv("MCP_HOST", "0.0.0.0"),
        "port": int(os.getenv("MCP_PORT", "9000")),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "database_path": os.getenv("DB_PATH", "./data/file_index.sqlite3"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "max_file_size": int(os.getenv("MAX_FILE_SIZE", "10485760")),  # 10MB
        "allowed_roots": [os.path.abspath(p) for p in os.getenv("ALLOWED_ROOTS", "").split(",") if p.strip()],
        "supported_extensions": [
            ".txt", ".md", ".py", ".js", ".ts", ".html", ".css", 
            ".json", ".xml", ".yaml", ".yml", ".csv", ".sql"
        ]
    }
