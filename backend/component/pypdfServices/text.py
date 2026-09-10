# pdf_service/text.py
"""
Text extraction with various modes and visitor functions
"""

from pypdf import PdfReader
from typing import Optional, Callable, List, Any
import os

__all__ = [
    "extract_text",
    "extract_text_layout",
    "extract_text_with_visitor",
    "extract_text_by_orientation",
    "extract_text_from_pages"
]


def extract_text(input_path: str, page_number: Optional[int] = None) -> str:
    """
    Extract text from PDF
    
    Args:
        page_number: Specific page (0-based), None for all pages
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    
    if page_number is not None:
        return reader.pages[page_number].extract_text()
    
    return "\n".join(page.extract_text() for page in reader.pages)


def extract_text_layout(
    input_path: str,
    page_number: Optional[int] = None,
    space_vertically: bool = True,
    scale_weight: float = 1.0,
    strip_rotated: bool = True
) -> str:
    """
    Extract text preserving layout
    
    Args:
        space_vertically: Remove blank lines
        scale_weight: Adjust horizontal spacing
        strip_rotated: Exclude rotated text
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    
    def extract_page(page):
        return page.extract_text(
            extraction_mode="layout",
            layout_mode_space_vertically=space_vertically,
            layout_mode_scale_weight=scale_weight,
            layout_mode_strip_rotated=strip_rotated
        )
    
    if page_number is not None:
        return extract_page(reader.pages[page_number])
    
    return "\n".join(extract_page(page) for page in reader.pages)


def extract_text_by_orientation(
    input_path: str,
    orientations: tuple = (0, 90, 180, 270),
    page_number: Optional[int] = None
) -> str:
    """
    Extract text by orientation
    
    Args:
        orientations: Tuple of angles to extract (0=up, 90=left, 180=down, 270=right)
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    
    def extract_page(page):
        return page.extract_text(orientations)
    
    if page_number is not None:
        return extract_page(reader.pages[page_number])
    
    return "\n".join(extract_page(page) for page in reader.pages)


def extract_text_from_pages(
    input_path: str,
    page_numbers: List[int]
) -> List[str]:
    """Extract text from specific pages"""
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    
    return [reader.pages[i].extract_text() for i in page_numbers]


def extract_text_with_visitor(
    input_path: str,
    visitor_text: Callable,
    visitor_operand_before: Optional[Callable] = None,
    visitor_operand_after: Optional[Callable] = None,
    page_number: Optional[int] = None
) -> str:
    """
    Extract text using visitor functions for fine-grained control
    
    Args:
        visitor_text: Function(text, cm, tm, font_dict, font_size)
        visitor_operand_before: Function(op, args, cm, tm)
        visitor_operand_after: Function(op, args, cm, tm)
        page_number: Specific page, None for all
    
    Example visitor_text:
        def visitor(text, cm, tm, font_dict, font_size):
            y = tm[5]  # vertical position
            if 50 < y < 720:  # ignore header/footer
                parts.append(text)
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    
    def extract_page(page):
        return page.extract_text(
            visitor_text=visitor_text,
            visitor_operand_before=visitor_operand_before,
            visitor_operand_after=visitor_operand_after
        )
    
    if page_number is not None:
        return extract_page(reader.pages[page_number])
    
    return "\n".join(extract_page(page) for page in reader.pages)


def _validate_file_exists(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")