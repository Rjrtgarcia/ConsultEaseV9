"""
Input sanitization utilities for ConsultEase.
Provides functions to sanitize and validate user inputs to prevent injection attacks.
"""
import re
import html
import logging
import os
import pathlib

logger = logging.getLogger(__name__)

def sanitize_string(input_str, allow_html=False, max_length=None):
    """
    Sanitize a string input to prevent injection attacks.
    
    Args:
        input_str: The input string to sanitize
        allow_html: Whether to allow HTML tags
        max_length: Maximum allowed length (truncates if longer)
        
    Returns:
        str: Sanitized input string
    """
    if input_str is None:
        return ""
    
    # Convert to string if not already
    if not isinstance(input_str, str):
        input_str = str(input_str)
    
    # Trim whitespace
    input_str = input_str.strip()
    
    # Truncate if too long
    if max_length and len(input_str) > max_length:
        input_str = input_str[:max_length]
        logger.warning(f"Input string truncated to {max_length} characters")
    
    # Escape HTML if not allowed
    if not allow_html:
        input_str = html.escape(input_str)
    
    # Escape SQL special characters
    input_str = input_str.replace("'", "''")
    
    return input_str

def sanitize_filename(filename):
    """
    Sanitize a filename to prevent path traversal attacks.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    if not filename:
        return ""
    
    # Convert to string if not already
    if not isinstance(filename, str):
        filename = str(filename)
    
    # Remove path separators and other dangerous characters
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    
    # Remove any path traversal attempts
    filename = os.path.basename(filename)
    
    # Ensure the filename is not empty after sanitization
    if not filename:
        filename = "unnamed_file"
    
    return filename

def sanitize_path(path, base_dir=None):
    """
    Sanitize a file path to prevent path traversal attacks.
    
    Args:
        path: The path to sanitize
        base_dir: Optional base directory to restrict paths to
        
    Returns:
        str: Sanitized path
    """
    if not path:
        return ""
    
    # Convert to string if not already
    if not isinstance(path, str):
        path = str(path)
    
    # Normalize the path
    path = os.path.normpath(path)
    
    # If base_dir is provided, ensure the path is within it
    if base_dir:
        base_dir = os.path.abspath(base_dir)
        path = os.path.abspath(os.path.join(base_dir, path))
        
        # Check if the path is within the base directory
        if not path.startswith(base_dir):
            logger.warning(f"Path traversal attempt detected: {path}")
            return base_dir
    
    return path

def sanitize_email(email):
    """
    Sanitize and validate an email address.
    
    Args:
        email: The email address to sanitize
        
    Returns:
        str: Sanitized email address or empty string if invalid
    """
    if not email:
        return ""
    
    # Convert to string if not already
    if not isinstance(email, str):
        email = str(email)
    
    # Trim whitespace
    email = email.strip().lower()
    
    # Validate email format
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        logger.warning(f"Invalid email format: {email}")
        return ""
    
    return email

def sanitize_integer(value, min_value=None, max_value=None, default=None):
    """
    Sanitize and validate an integer value.
    
    Args:
        value: The value to sanitize
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        default: Default value if conversion fails
        
    Returns:
        int: Sanitized integer value or default if invalid
    """
    try:
        # Convert to integer
        result = int(value)
        
        # Apply range constraints
        if min_value is not None and result < min_value:
            logger.warning(f"Integer value {result} below minimum {min_value}, using minimum")
            result = min_value
        
        if max_value is not None and result > max_value:
            logger.warning(f"Integer value {result} above maximum {max_value}, using maximum")
            result = max_value
        
        return result
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert '{value}' to integer, using default {default}")
        return default

def sanitize_boolean(value, default=False):
    """
    Sanitize and validate a boolean value.
    
    Args:
        value: The value to sanitize
        default: Default value if conversion fails
        
    Returns:
        bool: Sanitized boolean value or default if invalid
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, (int, float)):
        return bool(value)
    
    if isinstance(value, str):
        value = value.strip().lower()
        if value in ('true', 'yes', '1', 'y', 't'):
            return True
        if value in ('false', 'no', '0', 'n', 'f'):
            return False
    
    logger.warning(f"Failed to convert '{value}' to boolean, using default {default}")
    return default
