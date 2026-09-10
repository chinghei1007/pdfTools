# pdf_service/outlines.py
"""
PDF outline/bookmark handling
"""

from pypdf import PdfReader, PdfWriter
from typing import List, Optional, Any
import os

__all__ = [
    "get_outlines",
    "add_outline",
    "add_nested_outline",
    "get_named_destinations",
    "get_page_labels"
]


def get_outlines(input_path: str) -> List[Any]:
    """
    Get PDF outline/bookmarks
    
    Returns:
        Nested list of outline items
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    return reader.outline


def add_outline(
    input_path: str,
    output_path: str,
    title: str,
    page_number: int,
    parent: Optional[Any] = None
) -> Any:
    """
    Add outline item
    
    Returns:
        The created outline item (for use as parent in nested outlines)
    """
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    outline_item = writer.add_outline_item(
        title=title,
        page_number=page_number,
        parent=parent
    )
    
    with open(output_path, "wb") as f:
        writer.write(f)
    
    return outline_item


def add_nested_outline(
    input_path: str,
    output_path: str,
    outline_structure: List[dict]
) -> None:
    """
    Add nested outline structure
    
    Args:
        outline_structure: List of dicts with 'title', 'page', and optional 'children'
                          Example: [
                              {"title": "Chapter 1", "page": 0, "children": [
                                  {"title": "Section 1.1", "page": 1}
                              ]}
                          ]
    """
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    def add_items(items, parent=None):
        for item in items:
            outline_item = writer.add_outline_item(
                title=item["title"],
                page_number=item["page"],
                parent=parent
            )
            if "children" in item:
                add_items(item["children"], outline_item)
    
    add_items(outline_structure)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def get_named_destinations(input_path: str) -> dict:
    """Get named destinations"""
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    return reader.named_destinations


def get_page_labels(input_path: str) -> List[str]:
    """Get page labels"""
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    return reader.page_labels


def _validate_file_exists(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")


def _ensure_output_dir(path: str) -> None:
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)