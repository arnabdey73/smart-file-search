"""
Security utilities for the backend API.
"""

import hashlib
import os
from typing import Optional
from .config import get_backend_config

def verify_api_key(api_key: str) -> bool:
    """
    Verify API key against configured keys.
    
    Args:
        api_key: API key to verify
        
    Returns:
        True if valid, False otherwise
    """
    config = get_backend_config()
    configured_keys = config.get("api_keys", [])
    
    if not configured_keys:
        return True  # No auth required if no keys configured
    
    # Remove empty keys
    valid_keys = [key.strip() for key in configured_keys if key.strip()]
    
    return api_key in valid_keys

def hash_api_key(api_key: str) -> str:
    """
    Hash API key for secure storage.
    
    Args:
        api_key: API key to hash
        
    Returns:
        Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()

def generate_api_key() -> str:
    """
    Generate a random API key.
    
    Returns:
        Generated API key
    """
    return os.urandom(32).hex()
