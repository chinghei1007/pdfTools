"""
Common helper functions for PDF services
"""

import os


def validate_file_exists(path: str) -> None:
    """
    Validate that a file exists
    
    Args:
        path: File path to check
        
    Raises:
        FileNotFoundError: If file does not exist
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")


def ensure_output_dir(path: str) -> None:
    """
    Ensure the output directory exists, create if necessary
    
    Args:
        path: File path (directory will be extracted from this)
    """
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
