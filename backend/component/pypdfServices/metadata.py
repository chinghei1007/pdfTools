# pdf_service/metadata.py
"""
PDF metadata extraction - basic and XMP
"""

from pypdf import PdfReader
from typing import Dict, Any, Optional
import os

__all__ = [
    "get_metadata",
    "get_xmp_metadata",
    "get_all_metadata"
]


def get_metadata(input_path: str) -> Dict[str, Any]:
    """
    Get basic PDF metadata (/Info dictionary)
    
    Returns:
        Dictionary with keys like /Title, /Author, /Subject, /Creator, /Producer, /CreationDate, /ModDate
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    return reader.metadata or {}


def get_xmp_metadata(input_path: str) -> Optional[Dict[str, Any]]:
    """
    Get XMP metadata (extensible metadata platform)
    
    Returns:
        Dictionary with XMP properties or None
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    xmp = reader.xmp_metadata
    
    if xmp is None:
        return None
    
    return {
        "dc_title": getattr(xmp, "dc_title", None),
        "dc_creator": getattr(xmp, "dc_creator", None),
        "dc_description": getattr(xmp, "dc_description", None),
        "dc_subject": getattr(xmp, "dc_subject", None),
        "pdf_keywords": getattr(xmp, "pdf_keywords", None),
        "pdf_producer": getattr(xmp, "pdf_producer", None),
        "xmp_create_date": getattr(xmp, "xmp_create_date", None),
        "xmp_modify_date": getattr(xmp, "xmp_modify_date", None),
        "pdf_pdfversion": getattr(xmp, "pdf_pdfversion", None)
    }


def get_all_metadata(input_path: str) -> Dict[str, Any]:
    """
    Get both basic and XMP metadata
    
    Returns:
        Dictionary with 'basic' and 'xmp' keys
    """
    return {
        "basic": get_metadata(input_path),
        "xmp": get_xmp_metadata(input_path)
    }


def _validate_file_exists(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")