# pdf_service/forms.py
"""
PDF form field handling - read and fill forms
"""

from pypdf import PdfReader, PdfWriter
from typing import Dict, Optional, Any
import os

__all__ = [
    "get_form_fields",
    "get_form_text_fields",
    "fill_form",
    "get_field_info"
]


def get_form_fields(input_path: str) -> Dict[str, Any]:
    """
    Get all form fields from PDF
    
    Returns:
        Dictionary of field names to values
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    return reader.get_fields() or {}


def get_form_text_fields(input_path: str) -> Dict[str, str]:
    """Get only text input fields"""
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    return reader.get_form_text_fields() or {}


def fill_form(
    input_path: str,
    output_path: str,
    field_values: Dict[str, Any],
    auto_regenerate: bool = True
) -> None:
    """
    Fill form fields with values
    
    Args:
        field_values: Dictionary mapping field names to values
        auto_regenerate: Automatically regenerate appearance streams
    """
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    writer.update_page_form_field_values(
        writer.pages[0],  # This applies to all pages
        field_values,
        auto_regenerate=auto_regenerate
    )
    
    with open(output_path, "wb") as f:
        writer.write(f)


def get_field_info(input_path: str, field_name: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific field
    
    Returns:
        Dictionary with field properties or None if not found
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    fields = reader.get_fields()
    
    if field_name in fields:
        field = fields[field_name]
        return {
            "name": field_name,
            "value": field.get("/V"),
            "type": field.get("/FT"),
            "flags": field.get("/Ff"),
            "default_value": field.get("/DV")
        }
    
    return None


def _validate_file_exists(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")


def _ensure_output_dir(path: str) -> None:
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)