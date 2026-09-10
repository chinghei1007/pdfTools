# pdf_service/images.py
"""
Image extraction from PDFs
"""

from pypdf import PdfReader
from typing import List, Optional
import os

__all__ = [
    "extract_images",
    "extract_images_from_page",
    "get_image_info",
    "check_image_on_page"
]


def extract_images(
    input_path: str,
    output_dir: str,
    page_number: Optional[int] = None
) -> List[str]:
    """
    Extract all images from PDF
    
    Returns:
        List of extracted image file paths
    """
    _validate_file_exists(input_path)
    _ensure_output_dir(os.path.join(output_dir, "dummy.jpg"))
    
    reader = PdfReader(input_path)
    output_paths = []
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    pages = [reader.pages[page_number]] if page_number is not None else reader.pages
    
    image_count = 0
    for page in pages:
        for image in page.images:
            image_count += 1
            out_path = os.path.join(
                output_dir,
                f"{base_name}_img_{image_count:03d}_{image.name}"
            )
            with open(out_path, "wb") as f:
                f.write(image.data)
            output_paths.append(out_path)
    
    return output_paths


def extract_images_from_page(
    input_path: str,
    output_dir: str,
    page_number: int
) -> List[str]:
    """Extract images from a specific page"""
    return extract_images(input_path, output_dir, page_number)


def get_image_info(input_path: str, page_number: Optional[int] = None) -> List[dict]:
    """
    Get information about images in PDF
    
    Returns:
        List of dicts with keys: name, size, page_number
    """
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    
    image_info = []
    pages = [reader.pages[page_number]] if page_number is not None else enumerate(reader.pages)
    
    for i, page in (pages if page_number is not None else enumerate(reader.pages)):
        for image in page.images:
            image_info.append({
                "name": image.name,
                "size": len(image.data),
                "page": i if page_number is None else page_number
            })
    
    return image_info


def check_image_on_page(input_path: str, page_number: int, image_index: int) -> bool:
    """Check if a specific image exists on a page"""
    _validate_file_exists(input_path)
    reader = PdfReader(input_path)
    
    if page_number >= len(reader.pages):
        return False
    
    page = reader.pages[page_number]
    return image_index < len(page.images)


def _validate_file_exists(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")


def _ensure_output_dir(path: str) -> None:
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)