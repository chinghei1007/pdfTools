# pdf_service/pages.py
"""
Page transformations: scale, crop, transform, merge pages
"""

from pypdf import PdfReader, PdfWriter, Transformation
from typing import Optional, Tuple, List
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from component.common import validate_file_exists, ensure_output_dir

__all__ = [
    "scale_page",
    "crop_page",
    "transform_page",
    "merge_pages_overlay",
    "merge_pages_underlay",
    "remove_pages",
    "insert_page",
    "reorder_pages"
]


def scale_page(
    input_path: str,
    output_path: str,
    scale_factor: Optional[float] = None,
    target_size: Optional[Tuple[float, float]] = None,
    page_number: Optional[int] = None
) -> None:
    """
    Scale page(s)
    
    Args:
        scale_factor: Scale by factor (e.g., 0.5 for 50%)
        target_size: Scale to specific dimensions (width, height)
        page_number: Specific page, None for all
    """
    validate_file_exists(input_path)
    ensure_output_dir(output_path)
    
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    for i, page in enumerate(reader.pages):
        if page_number is None or i == page_number:
            if scale_factor:
                page.scale_by(scale_factor)
            elif target_size:
                page.scale_to(target_size[0], target_size[1])
        writer.add_page(page)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def crop_page(
    input_path: str,
    output_path: str,
    crop_box: Tuple[float, float, float, float],
    page_number: Optional[int] = None
) -> None:
    """
    Crop page(s)
    
    Args:
        crop_box: (x_min, y_min, x_max, y_max)
        page_number: Specific page, None for all
    """
    validate_file_exists(input_path)
    ensure_output_dir(output_path)
    
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    x_min, y_min, x_max, y_max = crop_box
    
    for i, page in enumerate(reader.pages):
        if page_number is None or i == page_number:
            page.cropbox.lower_left = (x_min, y_min)
            page.cropbox.upper_right = (x_max, y_max)
        writer.add_page(page)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def transform_page(
    input_path: str,
    output_path: str,
    rotate: float = 0,
    scale: float = 1.0,
    translate_x: float = 0,
    translate_y: float = 0,
    page_number: Optional[int] = None
) -> None:
    """
    Apply affine transformation to page(s)
    
    Args:
        rotate: Rotation in degrees
        scale: Scale factor
        translate_x: Horizontal translation
        translate_y: Vertical translation
        page_number: Specific page, None for all
    """
    validate_file_exists(input_path)
    ensure_output_dir(output_path)
    
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    transformation = Transformation()
    if rotate:
        transformation = transformation.rotate(rotate)
    if scale != 1.0:
        transformation = transformation.scale(scale)
    if translate_x or translate_y:
        transformation = transformation.translate(translate_x, translate_y)
    
    for i, page in enumerate(reader.pages):
        if page_number is None or i == page_number:
            page.add_transformation(transformation)
        writer.add_page(page)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def merge_pages_overlay(
    base_path: str,
    overlay_path: str,
    output_path: str,
    overlay_page: int = 0
) -> None:
    """Merge overlay page onto all pages of base PDF"""
    validate_file_exists(base_path)
    validate_file_exists(overlay_path)
    ensure_output_dir(output_path)
    
    reader = PdfReader(base_path)
    overlay = PdfReader(overlay_path).pages[overlay_page]
    
    writer = PdfWriter()
    for page in reader.pages:
        page.merge_page(overlay)
        writer.add_page(page)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def merge_pages_underlay(
    base_path: str,
    underlay_path: str,
    output_path: str,
    underlay_page: int = 0
) -> None:
    """Merge underlay page behind all pages of base PDF"""
    validate_file_exists(base_path)
    validate_file_exists(underlay_path)
    ensure_output_dir(output_path)
    
    reader = PdfReader(base_path)
    underlay = PdfReader(underlay_path).pages[underlay_page]
    
    writer = PdfWriter()
    for page in reader.pages:
        page.merge_page(underlay, over=False)
        writer.add_page(page)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def remove_pages(
    input_path: str,
    output_path: str,
    page_numbers: List[int]
) -> None:
    """Remove specific pages from PDF"""
    validate_file_exists(input_path)
    ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    # Remove in reverse order to maintain indices
    for page_num in sorted(page_numbers, reverse=True):
        writer.remove_page(page_num)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def insert_page(
    input_path: str,
    insert_path: str,
    output_path: str,
    position: int,
    insert_page_num: int = 0
) -> None:
    """Insert a page at specific position"""
    validate_file_exists(input_path)
    validate_file_exists(insert_path)
    ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    insert_reader = PdfReader(insert_path)
    insert_page_obj = insert_reader.pages[insert_page_num]
    
    writer.insert_page(insert_page_obj, index=position)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def reorder_pages(
    input_path: str,
    output_path: str,
    new_order: List[int]
) -> None:
    """
    Reorder pages
    
    Args:
        new_order: List of page indices in desired order, e.g., [2, 0, 1]
    """
    validate_file_exists(input_path)
    ensure_output_dir(output_path)
    
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    for page_num in new_order:
        writer.add_page(reader.pages[page_num])
    
    with open(output_path, "wb") as f:
        writer.write(f)