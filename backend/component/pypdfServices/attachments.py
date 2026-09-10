# pdf_service/attachments.py
"""
PDF attachment handling - embedded files
"""

from pypdf import PdfReader, PdfWriter
from typing import List, Dict, Optional
import os

__all__ = [
    "extract_attachments",
    "add_attachment",
    "get_attachment_list",
    "remove_attachments"
]


def extract_attachments(
    input_path: str,
    output_dir: str
) -> List[str]:
    """
    Extract all attachments from PDF
    
    Returns:
        List of extracted file paths
    """
    _validate_file_exists(input_path)
    _ensure_output_dir(os.path.join(output_dir, "dummy.txt"))
    
    reader = PdfReader(input_path)
    output_paths = []
    
    for name, content_list in reader.attachments.items():
        for i, content in enumerate(content_list):
            if len(content_list) > 1:
                base, ext = os.path.splitext(name)
                out_name = f"{base}_{i}{ext}"
            else:
                out_name = name
            
            out_path = os.path.join(output_dir, out_name)
            with open(out_path, "wb") as f:
                f.write(content)
            output_paths.append(out_path)
    
    return output_paths


def add_attachment(
    input_path: str,
    output_path: str,
    attachment_path: str,
    attachment_name: Optional[str] = None
) -> None:
    """
    Add attachment to PDF
    
    Args:
        attachment_path: Path to file to attach
        attachment_name: Name in PDF (defaults to filename)
    """
    _validate_file_exists(input_path)
    _validate_file_exists(attachment_path)
    _ensure_output_dir(output_path)
    
    if attachment_name is None:
        attachment_name = os.path.basename(attachment_path)
    
    with open(attachment_path, "rb") as f:
        attachment_data = f.read()
    
    writer = PdfWriter()
    writer.append(input_path)
    writer.add_attachment(attachment_name, attachment_data)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def get_attachment_list(input_path: str) -> List[Dict[str, any]]:
    """
    Get list of attachments
    
    Returns:
        List of dicts with 'name' and 'size' keys
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    
    attachments = []
    for name, content_list in reader.attachments.items():
        for content in content_list:
            attachments.append({
                "name": name,
                "size": len(content)
            })
    
    return attachments


def remove_attachments(
    input_path: str,
    output_path: str
) -> None:
    """Remove all attachments from PDF"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
    
    # Copy metadata but not attachments
    if reader.metadata:
        writer.add_metadata(reader.metadata)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def _validate_file_exists(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")


def _ensure_output_dir(path: str) -> None:
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)