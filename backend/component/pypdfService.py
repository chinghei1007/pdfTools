"""
Core PDF operations: merge, split, encrypt, decrypt, rotate
"""

from pypdf import PdfReader, PdfWriter
from typing import List, Optional, Union
import os

__all__ = [
    "merge_pdfs",
    "split_pdf",
    "split_pdf_by_ranges",
    "rotate_pages",
    "add_password",
    "remove_password",
    "flatten_pdf"
]


def merge_pdfs(
    input_paths: List[str],
    output_path: str,
    page_ranges: Optional[List[tuple]] = None
) -> None:
    """
    Merge multiple PDF files
    
    Args:
        input_paths: List of PDF file paths
        output_path: Output file path
        page_ranges: Optional list of (start, end) tuples for each input
                    Example: [(0, 5), (2, 10)] means pages 0-4 from first, 2-9 from second
    """
    _ensure_output_dir(output_path)
    writer = PdfWriter()
    
    for i, path in enumerate(input_paths):
        _validate_file_exists(path)
        if page_ranges and i < len(page_ranges):
            start, end = page_ranges[i]
            writer.append(path, pages=(start, end))
        else:
            writer.append(path)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def split_pdf(input_path: str, output_dir: str) -> List[str]:
    """Split PDF into single-page files"""
    _validate_file_exists(input_path)
    _ensure_output_dir(os.path.join(output_dir, "dummy.pdf"))
    
    reader = PdfReader(input_path)
    output_paths = []
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        out_path = os.path.join(output_dir, f"{base_name}_page_{i+1:03d}.pdf")
        with open(out_path, "wb") as f:
            writer.write(f)
        output_paths.append(out_path)
    
    return output_paths


def split_pdf_by_ranges(
    input_path: str,
    output_dir: str,
    ranges: List[tuple]
) -> List[str]:
    """
    Split PDF by page ranges
    
    Args:
        ranges: List of (start, end) tuples, e.g., [(0, 5), (5, 10), (10, None)]
    """
    _validate_file_exists(input_path)
    _ensure_output_dir(os.path.join(output_dir, "dummy.pdf"))
    
    reader = PdfReader(input_path)
    output_paths = []
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    for i, (start, end) in enumerate(ranges):
        writer = PdfWriter()
        if end is None:
            writer.append(input_path, pages=(start, len(reader.pages)))
        else:
            writer.append(input_path, pages=(start, end))
        
        out_path = os.path.join(output_dir, f"{base_name}_part_{i+1:03d}.pdf")
        with open(out_path, "wb") as f:
            writer.write(f)
        output_paths.append(out_path)
    
    return output_paths


def rotate_pages(
    input_path: str,
    output_path: str,
    degrees: int,
    page_numbers: Optional[List[int]] = None
) -> None:
    """
    Rotate PDF pages
    
    Args:
        degrees: 90, 180, or 270
        page_numbers: List of page indices (0-based), None for all pages
    """
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    for i, page in enumerate(reader.pages):
        if page_numbers is None or i in page_numbers:
            page.rotate(degrees)
        writer.add_page(page)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def add_password(
    input_path: str,
    output_path: str,
    user_password: str,
    owner_password: Optional[str] = None,
    permissions_flag: int = -1
) -> None:
    """
    Add password protection to PDF
    
    Args:
        user_password: Password for opening the PDF
        owner_password: Password for full access (defaults to user_password)
        permissions_flag: Permission flags (-1 for all permissions)
    """
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
    
    if owner_password is None:
        owner_password = user_password
    
    writer.encrypt(
        user_password=user_password,
        owner_password=owner_password,
        permissions_flag=permissions_flag
    )
    
    with open(output_path, "wb") as f:
        writer.write(f)


def remove_password(
    input_path: str,
    output_path: str,
    password: str
) -> None:
    """Remove password protection from PDF"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    reader = PdfReader(input_path)
    if reader.is_encrypted:
        reader.decrypt(password)
    
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def flatten_pdf(input_path: str, output_path: str) -> None:
    """Flatten PDF (merge form fields into content)"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    writer.flatten()
    
    with open(output_path, "wb") as f:
        writer.write(f)


# Helper functions
def _validate_file_exists(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")


def _ensure_output_dir(path: str) -> None:
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)