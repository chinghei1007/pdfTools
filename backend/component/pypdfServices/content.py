# pdf_service/content.py
"""
Low-level content stream access and manipulation
"""

from pypdf import PdfReader
from pypdf.generic import ContentStream
from typing import Callable, Optional, List, Tuple, Any
import os

__all__ = [
    "get_content_stream",
    "iterate_operations",
    "extract_drawing_operators",
    "extract_rectangles",
    "extract_lines"
]


def get_content_stream(input_path: str, page_number: int = 0) -> bytes:
    """
    Get raw content stream data
    
    Returns:
        Decoded content stream as bytes
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    page = reader.pages[page_number]
    
    contents = page.get_contents()
    if contents:
        return contents.get_data()
    return b""


def iterate_operations(
    input_path: str,
    page_number: int = 0,
    callback: Optional[Callable] = None
) -> List[Tuple[List[Any], bytes]]:
    """
    Iterate through all operations in content stream
    
    Args:
        callback: Function(operands, operator) called for each operation
    
    Returns:
        List of (operands, operator) tuples
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    page = reader.pages[page_number]
    
    contents = page.get_contents()
    if not contents:
        return []
    
    content_stream = ContentStream(contents, reader)
    operations = []
    
    for operands, operator in content_stream.operations:
        operations.append((operands, operator))
        if callback:
            callback(operands, operator)
    
    return operations


def extract_drawing_operators(
    input_path: str,
    page_number: int = 0
) -> List[Tuple[List[Any], bytes]]:
    """
    Extract drawing-related operators
    
    Returns:
        List of (operands, operator) for drawing operations
    """
    drawing_ops = {b"re", b"m", b"l", b"c", b"v", b"y", b"h", b"f", b"F", b"B", b"S"}
    
    operations = iterate_operations(input_path, page_number)
    return [(ops, op) for ops, op in operations if op in drawing_ops]


def extract_rectangles(
    input_path: str,
    page_number: int = 0
) -> List[Tuple[float, float, float, float]]:
    """
    Extract all rectangles from page
    
    Returns:
        List of (x, y, width, height) tuples
    """
    operations = iterate_operations(input_path, page_number)
    rectangles = []
    
    for operands, operator in operations:
        if operator == b"re" and len(operands) >= 4:
            x = float(operands[0])
            y = float(operands[1])
            w = float(operands[2])
            h = float(operands[3])
            rectangles.append((x, y, w, h))
    
    return rectangles


def extract_lines(
    input_path: str,
    page_number: int = 0
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    Extract all lines from page
    
    Returns:
        List of ((x1, y1), (x2, y2)) tuples
    """
    operations = iterate_operations(input_path, page_number)
    lines = []
    current_point = None
    
    for operands, operator in operations:
        if operator == b"m" and len(operands) >= 2:  # moveto
            current_point = (float(operands[0]), float(operands[1]))
        elif operator == b"l" and len(operands) >= 2 and current_point:  # lineto
            end_point = (float(operands[0]), float(operands[1]))
            lines.append((current_point, end_point))
            current_point = end_point
    
    return lines


def _validate_file_exists(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")