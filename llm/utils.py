"""
Utility functions for LLM module.
Helper functions for prompt loading and content sanitization.
"""

import os
import re
from pathlib import Path
from typing import Optional


def load_prompt_template(template_name: str) -> str:
    """
    Load a prompt template from the templates directory.
    
    Args:
        template_name: Name of the template file
        
    Returns:
        Template content as string
        
    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    template_path = Path(__file__).parent / "prompt_templates" / template_name
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Error reading template {template_name}: {e}")


def sanitize_content(content: str, max_length: int = 500) -> str:
    """
    Sanitize content for safe use in LLM prompts.
    
    Args:
        content: Input content to sanitize
        max_length: Maximum length of output
        
    Returns:
        Sanitized content
    """
    if not content:
        return ""
    
    # Remove potential sensitive patterns
    sanitized = content
    
    # Email addresses
    sanitized = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL]',
        sanitized
    )
    
    # Potential API keys/tokens (20+ alphanumeric chars)
    sanitized = re.sub(
        r'\b[A-Z0-9]{20,}\b',
        '[TOKEN]',
        sanitized
    )
    
    # Credit card numbers
    sanitized = re.sub(
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        '[CARD]',
        sanitized
    )
    
    # Social security numbers
    sanitized = re.sub(
        r'\b\d{3}-?\d{2}-?\d{4}\b',
        '[SSN]',
        sanitized
    )
    
    # Clean up whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized


def extract_code_snippets(content: str, language: Optional[str] = None) -> list:
    """
    Extract code snippets from content.
    
    Args:
        content: Content to extract from
        language: Optional language filter
        
    Returns:
        List of code snippets
    """
    snippets = []
    
    # Markdown code blocks
    if language:
        pattern = f"```{language}\\n(.*?)\\n```"
    else:
        pattern = r"```(\w+)?\n(.*?)\n```"
    
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        if language:
            snippets.append(match)
        else:
            # match is (language, code) tuple
            snippets.append(match[1] if len(match) > 1 else match[0])
    
    return snippets


def count_tokens_estimate(text: str) -> int:
    """
    Rough estimate of token count for text.
    Uses simple heuristic: ~4 characters per token.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', text.strip())
    
    # Rough estimate: 4 characters per token
    return len(cleaned) // 4


def truncate_to_tokens(text: str, max_tokens: int = 1000) -> str:
    """
    Truncate text to approximate token limit.
    
    Args:
        text: Input text
        max_tokens: Maximum token count
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    estimated_tokens = count_tokens_estimate(text)
    
    if estimated_tokens <= max_tokens:
        return text
    
    # Calculate character limit (rough estimate)
    char_limit = max_tokens * 4
    
    if len(text) <= char_limit:
        return text
    
    # Truncate and try to end at word boundary
    truncated = text[:char_limit]
    
    # Find last word boundary
    last_space = truncated.rfind(' ')
    if last_space > char_limit * 0.8:  # Don't go too far back
        truncated = truncated[:last_space]
    
    return truncated + "..."


def format_file_path(path: str, max_length: int = 60) -> str:
    """
    Format file path for display, truncating if too long.
    
    Args:
        path: File path to format
        max_length: Maximum display length
        
    Returns:
        Formatted path
    """
    if len(path) <= max_length:
        return path
    
    # Try to keep filename and some parent directories
    parts = Path(path).parts
    
    if len(parts) <= 2:
        return path
    
    # Start with filename
    filename = parts[-1]
    parent = parts[-2]
    
    if len(filename) + len(parent) + 3 <= max_length:
        result = f".../{parent}/{filename}"
    else:
        # Just show filename with truncation
        if len(filename) <= max_length - 3:
            result = f".../{filename}"
        else:
            result = f".../{filename[:max_length-6]}..."
    
    return result
