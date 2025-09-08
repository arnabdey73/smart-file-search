"""
Configuration for UI backend.
"""

import os
from typing import Dict, Any

def get_backend_config() -> Dict[str, Any]:
    """Get backend configuration."""
    return {
        "host": os.getenv("UI_BACKEND_HOST", "0.0.0.0"),
        "port": int(os.getenv("UI_BACKEND_PORT", "8081")),
        "mcp_server_url": os.getenv("MCP_SERVER_URL", "http://localhost:9000"),
        "mcp_timeout": int(os.getenv("MCP_TIMEOUT", "30")),
        "require_auth": os.getenv("REQUIRE_AUTH", "false").lower() == "true",
        "api_keys": os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else [],
        "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
        "max_request_size": int(os.getenv("MAX_REQUEST_SIZE", "1048576")),  # 1MB
        "rate_limit": int(os.getenv("RATE_LIMIT", "60")),  # requests per minute
    }
