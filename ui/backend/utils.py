"""
Utility functions for the backend API.
"""

import json
import logging
from typing import Dict, Any
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

def format_error_response(message: str, status_code: int, details: str = None) -> JSONResponse:
    """
    Format error response in consistent JSON structure.
    
    Args:
        message: Error message
        status_code: HTTP status code
        details: Optional additional details
        
    Returns:
        JSONResponse with error information
    """
    error_data = {
        "error": {
            "message": message,
            "status_code": status_code
        }
    }
    
    if details:
        error_data["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )

def log_request(request: Request):
    """
    Log incoming request details.
    
    Args:
        request: FastAPI request object
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"IP: {client_ip} - "
        f"User-Agent: {user_agent}"
    )

def sanitize_file_path(path: str) -> str:
    """
    Sanitize file path to prevent directory traversal.
    
    Args:
        path: File path to sanitize
        
    Returns:
        Sanitized path
    """
    # Remove any ../ attempts
    import os
    return os.path.normpath(path).replace("..", "")

def validate_search_params(query: str, k: int, offset: int) -> Dict[str, Any]:
    """
    Validate search parameters.
    
    Args:
        query: Search query
        k: Number of results
        offset: Results offset
        
    Returns:
        Validation result
    """
    errors = []
    
    if not query or not query.strip():
        errors.append("Query cannot be empty")
    
    if k < 1 or k > 100:
        errors.append("k must be between 1 and 100")
    
    if offset < 0:
        errors.append("offset must be non-negative")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
