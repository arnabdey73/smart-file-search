"""
Utility functions for the MCP server.
Common helper functions and utilities.
"""

import os
import hashlib
from pathlib import Path
from typing import List, Optional

def get_file_hash(file_path: str) -> str:
    """
    Calculate MD5 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash string
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def is_supported_file(file_path: str, supported_extensions: List[str]) -> bool:
    """
    Check if file extension is supported.
    
    Args:
        file_path: Path to the file
        supported_extensions: List of supported file extensions
        
    Returns:
        True if file is supported, False otherwise
    """
    return Path(file_path).suffix.lower() in supported_extensions

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def validate_path(path: str) -> Optional[str]:
    """
    Validate and normalize a file/directory path.
    
    Args:
        path: Path to validate
        
    Returns:
        Normalized path or None if invalid
    """
    try:
        normalized_path = os.path.normpath(os.path.abspath(path))
        if os.path.exists(normalized_path):
            return normalized_path
        return None
    except Exception:
        return None
