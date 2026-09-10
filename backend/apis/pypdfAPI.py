"""
PyPDF Services API - FastAPI endpoints for PDF operations
"""
import os
import sys
import uuid
import hashlib
import tempfile
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query, Path, Form
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import asyncio

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PDF services
from component.pypdfServices import basic, text, images, pages, annotations, metadata, outlines, formHandling, content, attachments

# Configuration
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "uploads")
PREVIEW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "previews")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "processed")

# Ensure directories exist
for dir_path in [UPLOAD_DIR, PREVIEW_DIR, OUTPUT_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Session storage (in production, use Redis or database)
sessions: Dict[str, dict] = {}

# Create FastAPI router
from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/pypdf", tags=["pypdf"])


# ==================== Pydantic Models ====================

class ProcessingRequest(BaseModel):
    """Base model for processing requests"""
    session_id: str
    page_numbers: Optional[List[int]] = None  # None means all pages
    
class TextExtractionRequest(ProcessingRequest):
    mode: str = "standard"  # standard, layout, orientation
    orientations: Optional[tuple] = (0, 90, 180, 270)
    
class ImageExtractionRequest(ProcessingRequest):
    pass

class MergeRequest(BaseModel):
    session_ids: List[str]
    output_session_id: str
    
class SplitRequest(ProcessingRequest):
    ranges: Optional[List[tuple]] = None
    
class RotateRequest(ProcessingRequest):
    degrees: int = 90
    page_numbers: Optional[List[int]] = None
    
class ScaleRequest(ProcessingRequest):
    scale_factor: Optional[float] = None
    target_size: Optional[tuple] = None
    
class CropRequest(ProcessingRequest):
    crop_box: tuple  # (x_min, y_min, x_max, y_max)
    
class AnnotationRequest(BaseModel):
    session_id: str
    page_number: int = 0
    annotation_type: str  # free_text, rectangle, ellipse, line, polygon, highlight, text, link
    params: Dict[str, Any]
    
class FormFillRequest(ProcessingRequest):
    field_values: Dict[str, Any]
    
class PreviewRequest(BaseModel):
    session_id: str
    page_number: Optional[int] = None  # None means all pages
    size: str = "small"  # small (100px) or large (hi-res)


# ==================== Helper Functions ====================

def get_session(session_id: str) -> dict:
    """Get session or raise error"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return sessions[session_id]

def validate_page_number(page_number: Optional[int], total_pages: int) -> int:
    """Validate and normalize page number"""
    if page_number is None:
        return 0  # Default to first page
    
    # Handle negative indices
    if page_number < 0:
        page_number = total_pages + page_number
    
    # Clamp to valid range
    if page_number < 0:
        return 0
    if page_number >= total_pages:
        return total_pages - 1
    
    return page_number

def generate_preview_image(pdf_path: str, page_num: int, size: str = "small") -> str:
    """
    Generate preview image for a PDF page
    Returns path to generated image
    """
    try:
        from pdf2image import convert_from_path
        from PIL import Image
        
        # Convert PDF page to image
        images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1, dpi=300 if size == "large" else 72)
        
        if not images:
            raise HTTPException(status_code=400, detail="Could not generate preview")
        
        img = images[0]
        
        # Resize based on size parameter
        if size == "small":
            # Longest edge 100px, ignoring ratio
            max_dim = max(img.size)
            scale = 100.0 / max_dim
            new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        # For large, keep original high resolution
        
        # Generate unique filename
        preview_id = uuid.uuid4().hex
        filename = f"preview_{preview_id}_{page_num}.png"
        filepath = os.path.join(PREVIEW_DIR, filename)
        
        img.save(filepath, "PNG")
        return filepath
        
    except ImportError:
        # Fallback: create a placeholder
        preview_id = uuid.uuid4().hex
        filename = f"preview_{preview_id}_{page_num}.png"
        filepath = os.path.join(PREVIEW_DIR, filename)
        
        # Create minimal PNG
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='gray')
        img.save(filepath, "PNG")
        return filepath

async def cleanup_session(session_id: str):
    """Clean up session files after expiration"""
    await asyncio.sleep(3600)  # 1 hour
    if session_id in sessions:
        session = sessions[session_id]
        # Clean up uploaded file
        if "file_path" in session and os.path.exists(session["file_path"]):
            os.remove(session["file_path"])
        # Clean up preview images
        if "previews" in session:
            for preview_path in session["previews"].values():
                if os.path.exists(preview_path):
                    os.remove(preview_path)
        del sessions[session_id]


# ==================== Upload/Download Endpoints ====================

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(..., description="PDF file to upload")):
    """
    Upload a PDF file for processing
    
    Returns session_id for subsequent operations
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Generate unique session ID
    session_id = uuid.uuid4().hex
    session_hash = hashlib.sha256(session_id.encode()).hexdigest()[:16]
    
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, f"{session_hash}_{file.filename}")
    
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Get page count
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        page_count = len(reader.pages)
        
        # Create session
        sessions[session_id] = {
            "id": session_id,
            "filename": file.filename,
            "file_path": file_path,
            "size_bytes": len(content),
            "page_count": page_count,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=24),
            "previews": {},
            "outputs": {}
        }
        
        # Start background task for cleanup
        asyncio.create_task(cleanup_session(session_id))
        
        return {
            "session_id": session_id,
            "filename": file.filename,
            "page_count": page_count,
            "size_bytes": len(content),
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/download/{session_id}")
async def download_pdf(session_id: str = Path(..., description="Session ID")):
    """
    Download the processed PDF file
    """
    session = get_session(session_id)
    
    # Check for output file first, then original
    file_path = session.get("output_path", session.get("file_path"))
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    filename = session.get("output_filename", session["filename"])
    
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/download/preview/{session_id}")
async def download_preview(
    session_id: str = Path(..., description="Session ID"),
    page_number: Optional[int] = Query(None, description="Page number (0-based). If not specified, returns first page"),
    size: str = Query("small", description="Preview size: small or large")
):
    """
    Download preview image for a PDF page
    
    If page_number not specified, returns first page (index 0)
    If page_number out of range, returns first or last page accordingly
    """
    session = get_session(session_id)
    
    # Validate page number with out-of-range handling
    total_pages = session["page_count"]
    if page_number is None:
        page_number = 0  # Default to first page
    elif page_number < 0:
        page_number = 0  # Out of range (negative) -> first page
    elif page_number >= total_pages:
        page_number = total_pages - 1  # Out of range (too high) -> last page
    
    # Check if preview exists, generate if not
    preview_key = f"{page_number}_{size}"
    if preview_key not in session["previews"]:
        preview_path = generate_preview_image(session["file_path"], page_number, size)
        session["previews"][preview_key] = preview_path
    
    preview_path = session["previews"][preview_key]
    
    if not os.path.exists(preview_path):
        raise HTTPException(status_code=404, detail="Preview not found")
    
    return FileResponse(
        path=preview_path,
        media_type="image/png",
        filename=f"preview_page_{page_number}_{size}.png"
    )


@router.get("/preview/all/{session_id}")
async def download_all_previews(
    session_id: str = Path(..., description="Session ID"),
    size: str = Query("small", description="Preview size: small or large")
):
    """
    Download all preview images for a PDF
    
    Returns all pages if no page_number specified
    """
    session = get_session(session_id)
    total_pages = session["page_count"]
    
    preview_paths = []
    for page_num in range(total_pages):
        preview_key = f"{page_num}_{size}"
        if preview_key not in session["previews"]:
            preview_path = generate_preview_image(session["file_path"], page_num, size)
            session["previews"][preview_key] = preview_path
        preview_paths.append(session["previews"][preview_key])
    
    return {
        "session_id": session_id,
        "total_pages": total_pages,
        "size": size,
        "preview_count": len(preview_paths),
        "message": "Previews generated. Use /download/preview/{session_id}?page_number=X&size=Y to download individual previews"
    }


# ==================== Text Extraction Endpoints ====================

@router.post("/extract/text")
async def extract_text(request: TextExtractionRequest):
    """
    Extract text from PDF
    
    Modes:
    - standard: Basic text extraction
    - layout: Preserve layout formatting
    - orientation: Extract by text orientation
    """
    session = get_session(request.session_id)
    file_path = session["file_path"]
    
    try:
        if request.mode == "layout":
            result = text.extract_text_layout(
                file_path,
                page_number=request.page_numbers[0] if request.page_numbers else None
            )
        elif request.mode == "orientation":
            result = text.extract_text_by_orientation(
                file_path,
                orientations=request.orientations,
                page_number=request.page_numbers[0] if request.page_numbers else None
            )
        else:  # standard
            result = text.extract_text(
                file_path,
                page_number=request.page_numbers[0] if request.page_numbers else None
            )
        
        return {
            "session_id": request.session_id,
            "text": result,
            "mode": request.mode
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")


# ==================== Image Extraction Endpoints ====================

@router.post("/extract/images")
async def extract_images(request: ImageExtractionRequest):
    """
    Extract images from PDF
    
    Returns list of extracted image paths (saved in output directory)
    """
    session = get_session(request.session_id)
    file_path = session["file_path"]
    
    output_subdir = os.path.join(OUTPUT_DIR, request.session_id, "images")
    os.makedirs(output_subdir, exist_ok=True)
    
    try:
        page_num = request.page_numbers[0] if request.page_numbers else None
        image_paths = images.extract_images(file_path, output_subdir, page_number=page_num)
        
        return {
            "session_id": request.session_id,
            "images": image_paths,
            "count": len(image_paths)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image extraction failed: {str(e)}")


# ==================== Basic Operations Endpoints ====================

@router.post("/merge")
async def merge_pdfs(request: MergeRequest):
    """
    Merge multiple PDFs
    
    Provide multiple session_ids to merge
    """
    # Validate all sessions exist
    input_paths = []
    filenames = []
    for sid in request.session_ids:
        sess = get_session(sid)
        input_paths.append(sess["file_path"])
        filenames.append(sess["filename"])
    
    output_filename = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, request.output_session_id, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        basic.merge_pdfs(input_paths, output_path)
        
        # Create output session
        sessions[request.output_session_id] = {
            "id": request.output_session_id,
            "filename": output_filename,
            "file_path": output_path,
            "output_path": output_path,
            "output_filename": output_filename,
            "created_at": datetime.now(),
            "source_sessions": request.session_ids
        }
        
        return {
            "output_session_id": request.output_session_id,
            "filename": output_filename,
            "merged_files": len(input_paths),
            "message": "PDFs merged successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")


@router.post("/split")
async def split_pdf(request: SplitRequest):
    """
    Split PDF into multiple files
    
    Can split by ranges or into single pages
    """
    session = get_session(request.session_id)
    file_path = session["file_path"]
    
    output_subdir = os.path.join(OUTPUT_DIR, request.session_id, "split")
    os.makedirs(output_subdir, exist_ok=True)
    
    try:
        if request.ranges:
            output_paths = basic.split_pdf_by_ranges(file_path, output_subdir, request.ranges)
        else:
            output_paths = basic.split_pdf_to_single_files(file_path, output_subdir)
        
        return {
            "session_id": request.session_id,
            "output_files": output_paths,
            "count": len(output_paths)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Split failed: {str(e)}")


@router.post("/rotate")
async def rotate_pages(request: RotateRequest):
    """
    Rotate PDF pages
    
    degrees: 90, 180, or 270
    """
    session = get_session(request.session_id)
    file_path = session["file_path"]
    
    output_filename = f"rotated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, request.session_id, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        basic.rotate_pages(file_path, output_path, request.degrees, request.page_numbers)
        
        # Update session with output
        session["output_path"] = output_path
        session["output_filename"] = output_filename
        
        return {
            "session_id": request.session_id,
            "output_path": output_path,
            "degrees": request.degrees,
            "message": "Pages rotated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rotation failed: {str(e)}")


@router.post("/encrypt")
async def encrypt_pdf(
    session_id: str,
    user_password: str,
    owner_password: Optional[str] = None
):
    """
    Add password protection to PDF
    """
    session = get_session(session_id)
    file_path = session["file_path"]
    
    output_filename = f"encrypted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, session_id, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        basic.add_password(file_path, output_path, user_password, owner_password)
        
        session["output_path"] = output_path
        session["output_filename"] = output_filename
        
        return {
            "session_id": session_id,
            "output_path": output_path,
            "message": "PDF encrypted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")


@router.post("/decrypt")
async def decrypt_pdf(session_id: str, password: str):
    """
    Remove password protection from PDF
    """
    session = get_session(session_id)
    file_path = session["file_path"]
    
    output_filename = f"decrypted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, session_id, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        basic.remove_password(file_path, output_path, password)
        
        session["output_path"] = output_path
        session["output_filename"] = output_filename
        
        return {
            "session_id": session_id,
            "output_path": output_path,
            "message": "PDF decrypted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decryption failed: {str(e)}")


# ==================== Page Operations Endpoints ====================

@router.post("/page/scale")
async def scale_page(request: ScaleRequest):
    """
    Scale PDF pages
    
    Either scale_factor OR target_size must be provided
    """
    session = get_session(request.session_id)
    file_path = session["file_path"]
    
    output_filename = f"scaled_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, request.session_id, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        pages.scale_page(
            file_path, 
            output_path, 
            scale_factor=request.scale_factor,
            target_size=request.target_size,
            page_number=request.page_numbers[0] if request.page_numbers else None
        )
        
        session["output_path"] = output_path
        session["output_filename"] = output_filename
        
        return {
            "session_id": request.session_id,
            "output_path": output_path,
            "message": "Page scaled successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scaling failed: {str(e)}")


@router.post("/page/crop")
async def crop_page(request: CropRequest):
    """
    Crop PDF pages
    
    crop_box: (x_min, y_min, x_max, y_max)
    """
    session = get_session(request.session_id)
    file_path = session["file_path"]
    
    output_filename = f"cropped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, request.session_id, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        pages.crop_page(
            file_path,
            output_path,
            request.crop_box,
            page_number=request.page_numbers[0] if request.page_numbers else None
        )
        
        session["output_path"] = output_path
        session["output_filename"] = output_filename
        
        return {
            "session_id": request.session_id,
            "output_path": output_path,
            "message": "Page cropped successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cropping failed: {str(e)}")


@router.post("/page/remove")
async def remove_pages(session_id: str, page_numbers: List[int]):
    """
    Remove specific pages from PDF
    """
    session = get_session(session_id)
    file_path = session["file_path"]
    
    output_filename = f"removed_pages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, session_id, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        pages.remove_pages(file_path, output_path, page_numbers)
        
        session["output_path"] = output_path
        session["output_filename"] = output_filename
        
        return {
            "session_id": session_id,
            "output_path": output_path,
            "removed_pages": page_numbers,
            "message": "Pages removed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Page removal failed: {str(e)}")


# ==================== Annotation Endpoints ====================

@router.post("/annotation/add")
async def add_annotation(request: AnnotationRequest):
    """
    Add annotation to PDF
    
    Supported types: free_text, rectangle, ellipse, line, polygon, highlight, text, link, uri_link
    
    Params vary by type - see function documentation
    """
    session = get_session(request.session_id)
    file_path = session["file_path"]
    
    output_filename = f"annotated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, request.session_id, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        if request.annotation_type == "free_text":
            annotations.add_free_text(
                file_path, output_path,
                text=request.params.get("text", ""),
                rect=tuple(request.params.get("rect", [0, 0, 100, 50])),
                page_number=request.page_number,
                font=request.params.get("font", "Helvetica"),
                font_size=request.params.get("font_size", "14pt"),
                font_color=request.params.get("font_color", "000000"),
                background_color=request.params.get("background_color", "ffffff"),
                bold=request.params.get("bold", False),
                italic=request.params.get("italic", False)
            )
        elif request.annotation_type == "rectangle":
            annotations.add_rectangle(
                file_path, output_path,
                rect=tuple(request.params.get("rect", [0, 0, 100, 50])),
                page_number=request.page_number,
                interior_color=request.params.get("interior_color"),
                border_color=request.params.get("border_color", "000000")
            )
        elif request.annotation_type == "ellipse":
            annotations.add_ellipse(
                file_path, output_path,
                rect=tuple(request.params.get("rect", [0, 0, 100, 50])),
                page_number=request.page_number,
                interior_color=request.params.get("interior_color")
            )
        elif request.annotation_type == "line":
            annotations.add_line(
                file_path, output_path,
                p1=tuple(request.params.get("p1", [0, 0])),
                p2=tuple(request.params.get("p2", [100, 100])),
                page_number=request.page_number,
                text=request.params.get("text", "")
            )
        elif request.annotation_type == "highlight":
            annotations.add_highlight(
                file_path, output_path,
                rect=tuple(request.params.get("rect", [0, 0, 100, 50])),
                page_number=request.page_number,
                highlight_color=request.params.get("highlight_color", "ffff00"),
                printing=request.params.get("printing", False)
            )
        elif request.annotation_type == "text":
            annotations.add_text_annotation(
                file_path, output_path,
                rect=tuple(request.params.get("rect", [0, 0, 50, 50])),
                text=request.params.get("text", ""),
                page_number=request.page_number,
                open_annotation=request.params.get("open", False)
            )
        elif request.annotation_type == "link":
            annotations.add_link(
                file_path, output_path,
                rect=tuple(request.params.get("rect", [0, 0, 100, 50])),
                target_page=request.params.get("target_page", 0),
                page_number=request.page_number
            )
        elif request.annotation_type == "uri_link":
            annotations.add_uri_link(
                file_path, output_path,
                rect=tuple(request.params.get("rect", [0, 0, 100, 50])),
                url=request.params.get("url", ""),
                page_number=request.page_number
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown annotation type: {request.annotation_type}")
        
        session["output_path"] = output_path
        session["output_filename"] = output_filename
        
        return {
            "session_id": request.session_id,
            "output_path": output_path,
            "annotation_type": request.annotation_type,
            "message": "Annotation added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Annotation failed: {str(e)}")


@router.get("/annotation/list/{session_id}")
async def list_annotations(
    session_id: str = Path(..., description="Session ID"),
    page_number: Optional[int] = Query(None, description="Specific page, None for all")
):
    """
    List all annotations in PDF
    """
    session = get_session(session_id)
    file_path = session.get("output_path", session["file_path"])
    
    try:
        annots = annotations.get_annotations(file_path, page_number)
        
        return {
            "session_id": session_id,
            "annotations": annots,
            "count": len(annots)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list annotations: {str(e)}")


# ==================== Form Handling Endpoints ====================

@router.get("/form/fields/{session_id}")
async def get_form_fields(session_id: str = Path(..., description="Session ID")):
    """
    Get all form fields from PDF
    """
    session = get_session(session_id)
    file_path = session.get("output_path", session["file_path"])
    
    try:
        fields = formHandling.get_form_fields(file_path)
        
        return {
            "session_id": session_id,
            "fields": fields
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get form fields: {str(e)}")


@router.post("/form/fill")
async def fill_form(request: FormFillRequest):
    """
    Fill PDF form fields
    """
    session = get_session(request.session_id)
    file_path = session.get("output_path", session["file_path"])
    
    output_filename = f"filled_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, request.session_id, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        formHandling.fill_form(file_path, output_path, request.field_values)
        
        session["output_path"] = output_path
        session["output_filename"] = output_filename
        
        return {
            "session_id": request.session_id,
            "output_path": output_path,
            "filled_fields": list(request.field_values.keys()),
            "message": "Form filled successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Form filling failed: {str(e)}")


# ==================== Metadata Endpoints ====================

@router.get("/metadata/{session_id}")
async def get_metadata(session_id: str = Path(..., description="Session ID")):
    """
    Get PDF metadata (basic and XMP)
    """
    session = get_session(session_id)
    file_path = session.get("output_path", session["file_path"])
    
    try:
        meta = metadata.get_all_metadata(file_path)
        
        return {
            "session_id": session_id,
            "metadata": meta
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metadata: {str(e)}")


# ==================== Outline/Bookmark Endpoints ====================

@router.get("/outline/{session_id}")
async def get_outlines(session_id: str = Path(..., description="Session ID")):
    """
    Get PDF outline/bookmarks
    """
    session = get_session(session_id)
    file_path = session.get("output_path", session["file_path"])
    
    try:
        outlines_list = outlines.get_outlines(file_path)
        
        return {
            "session_id": session_id,
            "outlines": outlines_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get outlines: {str(e)}")


@router.post("/outline/add")
async def add_outline(
    session_id: str,
    title: str,
    page_number: int,
    parent: Optional[Any] = None
):
    """
    Add outline/bookmark to PDF
    """
    session = get_session(session_id)
    file_path = session.get("output_path", session["file_path"])
    
    output_filename = f"outlined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, session_id, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        outline_item = outlines.add_outline(file_path, output_path, title, page_number, parent)
        
        session["output_path"] = output_path
        session["output_filename"] = output_filename
        
        return {
            "session_id": session_id,
            "output_path": output_path,
            "outline_added": title,
            "message": "Outline added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add outline: {str(e)}")


# ==================== Attachment Endpoints ====================

@router.get("/attachments/{session_id}")
async def get_attachments(session_id: str = Path(..., description="Session ID")):
    """
    Get list of attachments in PDF
    """
    session = get_session(session_id)
    file_path = session.get("output_path", session["file_path"])
    
    try:
        attachments_list = attachments.get_attachment_list(file_path)
        
        return {
            "session_id": session_id,
            "attachments": attachments_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get attachments: {str(e)}")


@router.post("/attachment/add")
async def add_attachment(
    session_id: str,
    attachment_file: UploadFile = File(...),
    attachment_name: Optional[str] = None
):
    """
    Add attachment to PDF
    """
    session = get_session(session_id)
    file_path = session.get("output_path", session["file_path"])
    
    # Save attachment temporarily
    temp_attachment = os.path.join(UPLOAD_DIR, f"temp_{uuid.uuid4().hex}_{attachment_file.filename}")
    with open(temp_attachment, "wb") as f:
        f.write(await attachment_file.read())
    
    output_filename = f"attached_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, session_id, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        attachments.add_attachment(file_path, output_path, temp_attachment, attachment_name)
        
        session["output_path"] = output_path
        session["output_filename"] = output_filename
        
        # Clean up temp file
        os.remove(temp_attachment)
        
        return {
            "session_id": session_id,
            "output_path": output_path,
            "attachment_name": attachment_name or attachment_file.filename,
            "message": "Attachment added successfully"
        }
        
    except Exception as e:
        if os.path.exists(temp_attachment):
            os.remove(temp_attachment)
        raise HTTPException(status_code=500, detail=f"Failed to add attachment: {str(e)}")


@router.post("/attachments/extract")
async def extract_attachments(session_id: str):
    """
    Extract all attachments from PDF
    """
    session = get_session(session_id)
    file_path = session.get("output_path", session["file_path"])
    
    output_subdir = os.path.join(OUTPUT_DIR, session_id, "attachments")
    os.makedirs(output_subdir, exist_ok=True)
    
    try:
        attachment_paths = attachments.extract_attachments(file_path, output_subdir)
        
        return {
            "session_id": session_id,
            "attachments": attachment_paths,
            "count": len(attachment_paths)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract attachments: {str(e)}")


# ==================== Session Management ====================

@router.get("/session/{session_id}")
async def get_session_info(session_id: str = Path(..., description="Session ID")):
    """
    Get session information
    """
    session = get_session(session_id)
    
    return {
        "session_id": session["id"],
        "filename": session["filename"],
        "page_count": session["page_count"],
        "size_bytes": session["size_bytes"],
        "created_at": session["created_at"].isoformat(),
        "expires_at": session["expires_at"].isoformat(),
        "has_output": "output_path" in session,
        "preview_count": len(session.get("previews", {}))
    }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str = Path(..., description="Session ID")):
    """
    Delete session and clean up files
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Clean up files
    for path_key in ["file_path", "output_path"]:
        if path_key in session and os.path.exists(session[path_key]):
            os.remove(session[path_key])
    
    for preview_path in session.get("previews", {}).values():
        if os.path.exists(preview_path):
            os.remove(preview_path)
    
    del sessions[session_id]
    
    return {"message": f"Session {session_id} deleted successfully"}


@router.get("/sessions")
async def list_sessions():
    """
    List all active sessions
    """
    now = datetime.now()
    active_sessions = []
    
    for sid, session in sessions.items():
        if session["expires_at"] > now:
            active_sessions.append({
                "session_id": sid,
                "filename": session["filename"],
                "page_count": session["page_count"],
                "created_at": session["created_at"].isoformat(),
                "expires_at": session["expires_at"].isoformat()
            })
    
    return {"active_sessions": active_sessions, "count": len(active_sessions)}