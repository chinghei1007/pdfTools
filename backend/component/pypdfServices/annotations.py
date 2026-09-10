# pdf_service/annotations.py
"""
PDF annotation handling - read and write various annotation types
"""

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import (
    FreeText, Rectangle, Ellipse, Line,
    Polygon, PolyLine, Highlight,
    Text, Link, Popup
)
from pypdf.generic import RectangleObject
from typing import List, Optional, Tuple, Union
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from component.common import validate_file_exists, ensure_output_dir

__all__ = [
    "add_free_text",
    "add_rectangle",
    "add_ellipse",
    "add_line",
    "add_polygon",
    "add_highlight",
    "add_text_annotation",
    "add_link",
    "add_uri_link",
    "get_annotations",
    "remove_annotations"
]


def add_free_text(
    input_path: str,
    output_path: str,
    text: str,
    rect: Tuple[float, float, float, float],
    page_number: int = 0,
    font: str = "Helvetica",
    font_size: str = "14pt",
    font_color: str = "000000",
    background_color: Optional[str] = "ffffff",
    bold: bool = False,
    italic: bool = False
) -> None:
    """Add free text annotation"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    annotation = FreeText(
        text=text,
        rect=RectangleObject(rect),
        font=font,
        font_size=font_size,
        font_color=font_color,
        background_color=background_color,
        bold=bold,
        italic=italic
    )
    
    writer.add_annotation(page_number=page_number, annotation=annotation)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def add_rectangle(
    input_path: str,
    output_path: str,
    rect: Tuple[float, float, float, float],
    page_number: int = 0,
    interior_color: Optional[str] = None,
    border_color: str = "000000"
) -> None:
    """Add rectangle annotation"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    annotation = Rectangle(
        rect=RectangleObject(rect),
        interior_color=interior_color
    )
    
    writer.add_annotation(page_number=page_number, annotation=annotation)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def add_ellipse(
    input_path: str,
    output_path: str,
    rect: Tuple[float, float, float, float],
    page_number: int = 0,
    interior_color: Optional[str] = None
) -> None:
    """Add ellipse/circle annotation"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    annotation = Ellipse(
        rect=RectangleObject(rect),
        interior_color=interior_color
    )
    
    writer.add_annotation(page_number=page_number, annotation=annotation)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def add_line(
    input_path: str,
    output_path: str,
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    page_number: int = 0,
    text: str = ""
) -> None:
    """Add line annotation"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    # Calculate bounding rect
    x_min = min(p1[0], p2[0])
    y_min = min(p1[1], p2[1])
    x_max = max(p1[0], p2[0])
    y_max = max(p1[1], p2[1])
    rect = (x_min, y_min, x_max, y_max)
    
    annotation = Line(
        p1=p1,
        p2=p2,
        rect=RectangleObject(rect),
        text=text
    )
    
    writer.add_annotation(page_number=page_number, annotation=annotation)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def add_polygon(
    input_path: str,
    output_path: str,
    vertices: List[Tuple[float, float]],
    page_number: int = 0
) -> None:
    """Add polygon annotation"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    # Calculate bounding rect
    x_coords = [v[0] for v in vertices]
    y_coords = [v[1] for v in vertices]
    rect = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
    
    annotation = Polygon(
        vertices=vertices,
        rect=RectangleObject(rect)
    )
    
    writer.add_annotation(page_number=page_number, annotation=annotation)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def add_highlight(
    input_path: str,
    output_path: str,
    rect: Tuple[float, float, float, float],
    page_number: int = 0,
    highlight_color: str = "ffff00",
    printing: bool = False
) -> None:
    """Add highlight annotation"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    # QuadPoints define the highlighted area (4 corners)
    x1, y1, x2, y2 = rect
    quad_points = [x1, y2, x2, y2, x1, y1, x2, y1]
    
    annotation = Highlight(
        rect=RectangleObject(rect),
        quad_points=quad_points,
        highlight_color=highlight_color,
        printing=printing
    )
    
    writer.add_annotation(page_number=page_number, annotation=annotation)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def add_text_annotation(
    input_path: str,
    output_path: str,
    rect: Tuple[float, float, float, float],
    text: str,
    page_number: int = 0,
    open_annotation: bool = False
) -> None:
    """Add text annotation (sticky note)"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    annotation = Text(
        rect=RectangleObject(rect),
        text=text,
        open=open_annotation
    )
    
    writer.add_annotation(page_number=page_number, annotation=annotation)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def add_link(
    input_path: str,
    output_path: str,
    rect: Tuple[float, float, float, float],
    target_page: int,
    page_number: int = 0
) -> None:
    """Add internal link to another page"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    annotation = Link(
        rect=RectangleObject(rect),
        target_page_index=target_page
    )
    
    writer.add_annotation(page_number=page_number, annotation=annotation)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def add_uri_link(
    input_path: str,
    output_path: str,
    rect: Tuple[float, float, float, float],
    url: str,
    page_number: int = 0
) -> None:
    """Add external URL link"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    writer = PdfWriter()
    writer.append(input_path)
    
    annotation = Link(
        rect=RectangleObject(rect),
        url=url
    )
    
    writer.add_annotation(page_number=page_number, annotation=annotation)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def get_annotations(
    input_path: str,
    page_number: Optional[int] = None
) -> List[dict]:
    """
    Get all annotations from PDF
    
    Returns:
        List of dicts with annotation info
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    
    annotations = []
    pages = [reader.pages[page_number]] if page_number is not None else reader.pages
    
    for i, page in enumerate(pages):
        if "/Annots" in page:
            annots = page["/Annots"]
            for annot in annots:
                annot_obj = annot.get_object()
                annotations.append({
                    "page": i if page_number is None else page_number,
                    "type": annot_obj.get("/Subtype", "Unknown"),
                    "rect": annot_obj.get("/Rect"),
                    "contents": annot_obj.get("/Contents", "")
                })
    
    return annotations


def remove_annotations(
    input_path: str,
    output_path: str,
    page_number: Optional[int] = None
) -> None:
    """Remove all annotations from PDF"""
    _validate_file_exists(input_path)
    _ensure_output_dir(output_path)
    
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    for i, page in enumerate(reader.pages):
        if page_number is not None and i != page_number:
            writer.add_page(page)
        else:
            # Create new page without annotations
            new_page = page
            if "/Annots" in new_page:
                del new_page["/Annots"]
            writer.add_page(new_page)
    
    with open(output_path, "wb") as f:
        writer.write(f)


def _validate_file_exists(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")


def _ensure_output_dir(path: str) -> None:
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)