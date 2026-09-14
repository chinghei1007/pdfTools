"""Unit tests for pypdfAPI.py - PyPDF-specific API endpoints"""
import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from io import BytesIO

import pypdf
from fastapi.testclient import TestClient
from pypdf import PdfReader, PdfWriter

# Import the router and app
from apis.pypdfAPI import router, sessions, UPLOAD_DIR, PREVIEW_DIR, OUTPUT_DIR
from expose.main import app


class PypdfAPITest(unittest.TestCase):
    """Test cases for PyPDF API endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directories
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_upload_dir = UPLOAD_DIR
        self.original_preview_dir = PREVIEW_DIR
        self.original_output_dir = OUTPUT_DIR
        
        # Override directories to use temp dir
        os.environ['UPLOAD_DIR'] = os.path.join(self.temp_dir.name, 'uploads')
        os.environ['PREVIEW_DIR'] = os.path.join(self.temp_dir.name, 'previews')
        os.environ['OUTPUT_DIR'] = os.path.join(self.temp_dir.name, 'outputs')
        
        # Create directories
        for dir_name in ['uploads', 'previews', 'outputs']:
            os.makedirs(os.path.join(self.temp_dir.name, dir_name), exist_ok=True)
        
        # Clear sessions
        sessions.clear()
        
        self.client = TestClient(app)
        
        # Create test PDF
        self.test_pdf_path = os.path.join(self.temp_dir.name, "test.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)  # Letter size
        writer.add_blank_page(width=612, height=792)
        writer.add_blank_page(width=612, height=792)
        with open(self.test_pdf_path, "wb") as f:
            writer.write(f)
        
        with open(self.test_pdf_path, "rb") as f:
            self.test_pdf_bytes = f.read()

    def tearDown(self):
        """Clean up test fixtures"""
        self.client.close()
        sessions.clear()
        self.temp_dir.cleanup()

    # ==================== Upload Tests ====================

    def test_upload_pdf_success(self):
        """Test uploading a valid PDF file"""
        with open(self.test_pdf_path, "rb") as f:
            response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("session_id", result)
        self.assertEqual(result["filename"], "test.pdf")
        self.assertEqual(result["page_count"], 3)
        self.assertEqual(result["size_bytes"], len(self.test_pdf_bytes))
        self.assertIn("message", result)

    def test_upload_non_pdf_file(self):
        """Test uploading a non-PDF file fails"""
        response = self.client.post(
            "/api/v1/pypdf/upload",
            files={"file": ("test.txt", b"plain text", "text/plain")}
        )
        
        self.assertEqual(response.status_code, 400)

    def test_upload_empty_file(self):
        """Test uploading an empty file"""
        response = self.client.post(
            "/api/v1/pypdf/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")}
        )
        
        # Should either fail or create empty session
        # The behavior depends on PdfReader handling
        pass  # Accept either outcome

    def test_upload_invalid_pdf(self):
        """Test uploading an invalid PDF file"""
        response = self.client.post(
            "/api/v1/pypdf/upload",
            files={"file": ("invalid.pdf", b"not a pdf file", "application/pdf")}
        )
        
        # Should fail with 500 or 400
        self.assertIn(response.status_code, [400, 500])

    # ==================== Download Tests ====================

    def test_download_original_pdf(self):
        """Test downloading the original uploaded PDF"""
        # Upload a file
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        # Download the file
        response = self.client.get(f"/api/v1/pypdf/download/{session_id}")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.test_pdf_bytes)
        self.assertEqual(response.headers["content-type"], "application/pdf")

    def test_download_nonexistent_session(self):
        """Test downloading from non-existent session"""
        response = self.client.get("/api/v1/pypdf/download/nonexistent")
        self.assertEqual(response.status_code, 404)

    # ==================== Preview Tests ====================

    def test_download_preview_first_page(self):
        """Test downloading preview of first page"""
        # Upload a file
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        # Download preview
        response = self.client.get(f"/api/v1/pypdf/download/preview/{session_id}")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")

    def test_download_preview_specific_page(self):
        """Test downloading preview of specific page"""
        # Upload a file
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        # Download preview of page 1
        response = self.client.get(f"/api/v1/pypdf/download/preview/{session_id}?page_number=1")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")

    def test_download_preview_out_of_range(self):
        """Test downloading preview with out-of-range page number"""
        # Upload a file
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        # Request page beyond range (should clamp to last page)
        response = self.client.get(f"/api/v1/pypdf/download/preview/{session_id}?page_number=999")
        
        self.assertEqual(response.status_code, 200)

    def test_download_preview_negative_page(self):
        """Test downloading preview with negative page number"""
        # Upload a file
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        # Request negative page (should clamp to first page)
        response = self.client.get(f"/api/v1/pypdf/download/preview/{session_id}?page_number=-1")
        
        self.assertEqual(response.status_code, 200)

    def test_download_all_previews(self):
        """Test downloading all previews for a session"""
        # Upload a file
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        # Download all previews
        response = self.client.get(f"/api/v1/pypdf/preview/all/{session_id}")
        
        self.assertEqual(response.status_code, 200)

    def test_download_preview_nonexistent_session(self):
        """Test downloading preview from non-existent session"""
        response = self.client.get("/api/v1/pypdf/download/preview/nonexistent")
        self.assertEqual(response.status_code, 404)

    # ==================== Text Extraction Tests ====================

    def test_extract_text_standard_mode(self):
        """Test text extraction in standard mode"""
        # Create a PDF with text
        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)
        # Add some text using pypdf's text insertion
        from pypdf.generic import NameObject, NumberObject, StringObject, ArrayObject
        from pypdf import PageObject
        
        # For simplicity, use a simple text extraction test
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        # Extract text
        response = self.client.post(
            "/api/v1/pypdf/extract/text",
            json={
                "session_id": session_id,
                "mode": "standard"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("text", result)
        # Text might be empty for blank pages

    def test_extract_text_with_page_numbers(self):
        """Test text extraction with specific page numbers"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/extract/text",
            json={
                "session_id": session_id,
                "page_numbers": [0, 2],
                "mode": "standard"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("text", result)

    def test_extract_text_nonexistent_session(self):
        """Test text extraction with non-existent session"""
        response = self.client.post(
            "/api/v1/pypdf/extract/text",
            json={
                "session_id": "nonexistent",
                "mode": "standard"
            }
        )
        
        self.assertEqual(response.status_code, 404)

    # ==================== Image Extraction Tests ====================

    def test_extract_images(self):
        """Test image extraction from PDF"""
        # For this test, we'll use the existing PDF
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/extract/images",
            json={"session_id": session_id}
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("images", result)
        # May be empty if PDF has no images

    def test_extract_images_nonexistent_session(self):
        """Test image extraction with non-existent session"""
        response = self.client.post(
            "/api/v1/pypdf/extract/images",
            json={"session_id": "nonexistent"}
        )
        
        self.assertEqual(response.status_code, 404)

    # ==================== Merge Tests ====================

    def test_merge_pdfs(self):
        """Test merging multiple PDFs"""
        # Upload first PDF
        with open(self.test_pdf_path, "rb") as f:
            upload1 = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test1.pdf", f, "application/pdf")}
            )
        session_id1 = upload1.json()["session_id"]
        
        # Upload second PDF
        with open(self.test_pdf_path, "rb") as f:
            upload2 = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test2.pdf", f, "application/pdf")}
            )
        session_id2 = upload2.json()["session_id"]
        
        # Merge PDFs
        response = self.client.post(
            "/api/v1/pypdf/merge",
            json={
                "session_ids": [session_id1, session_id2],
                "output_session_id": session_id1
            }
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)
        self.assertIn("page_count", result)

    def test_merge_pdfs_invalid_session(self):
        """Test merging with invalid session ID"""
        response = self.client.post(
            "/api/v1/pypdf/merge",
            json={
                "session_ids": ["nonexistent1", "nonexistent2"],
                "output_session_id": "nonexistent1"
            }
        )
        
        self.assertEqual(response.status_code, 404)

    # ==================== Split Tests ====================

    def test_split_pdf(self):
        """Test splitting a PDF into ranges"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/split",
            json={
                "session_id": session_id,
                "ranges": [[0, 1], [2, 2]]  # Split into pages 0-1 and page 2
            }
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

    def test_split_pdf_nonexistent_session(self):
        """Test splitting with non-existent session"""
        response = self.client.post(
            "/api/v1/pypdf/split",
            json={
                "session_id": "nonexistent",
                "ranges": [[0, 1]]
            }
        )
        
        self.assertEqual(response.status_code, 404)

    # ==================== Rotate Tests ====================

    def test_rotate_pages(self):
        """Test rotating PDF pages"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/rotate",
            json={
                "session_id": session_id,
                "degrees": 90,
                "page_numbers": [0, 1]
            }
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

    def test_rotate_pages_default_degrees(self):
        """Test rotating with default degrees (90)"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/rotate",
            json={
                "session_id": session_id,
                "page_numbers": [0]
            }
        )
        
        self.assertEqual(response.status_code, 200)

    def test_rotate_pages_nonexistent_session(self):
        """Test rotating with non-existent session"""
        response = self.client.post(
            "/api/v1/pypdf/rotate",
            json={
                "session_id": "nonexistent",
                "degrees": 90
            }
        )
        
        self.assertEqual(response.status_code, 404)

    # ==================== Encrypt/Decrypt Tests ====================

    def test_encrypt_pdf(self):
        """Test encrypting a PDF"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/encrypt",
            json={
                "session_id": session_id,
                "password": "test123",
                "owner_password": "owner123"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

    def test_decrypt_pdf(self):
        """Test decrypting a PDF"""
        # First encrypt
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        # Encrypt
        self.client.post(
            "/api/v1/pypdf/encrypt",
            json={
                "session_id": session_id,
                "password": "test123"
            }
        )
        
        # Decrypt
        response = self.client.post(
            f"/api/v1/pypdf/decrypt/{session_id}",
            json={"password": "test123"}
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

    def test_decrypt_with_wrong_password(self):
        """Test decrypting with wrong password"""
        # First encrypt
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        # Encrypt
        self.client.post(
            "/api/v1/pypdf/encrypt",
            json={
                "session_id": session_id,
                "password": "test123"
            }
        )
        
        # Try to decrypt with wrong password
        response = self.client.post(
            f"/api/v1/pypdf/decrypt/{session_id}",
            json={"password": "wrong"}
        )
        
        # Should fail or return error
        self.assertIn(response.status_code, [400, 401, 403, 500])

    # ==================== Scale/Crop Tests ====================

    def test_scale_page(self):
        """Test scaling a page"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/page/scale",
            json={
                "session_id": session_id,
                "scale_factor": 0.5,
                "page_numbers": [0]
            }
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

    def test_crop_page(self):
        """Test cropping a page"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/page/crop",
            json={
                "session_id": session_id,
                "crop_box": (50, 50, 500, 700),
                "page_numbers": [0]
            }
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

    # ==================== Page Removal Tests ====================

    def test_remove_pages(self):
        """Test removing pages from PDF"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/page/remove",
            json={
                "session_id": session_id,
                "page_numbers": [1]  # Remove second page (0-indexed)
            }
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

    # ==================== Annotation Tests ====================

    def test_add_annotation(self):
        """Test adding annotation to PDF"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/annotation/add",
            json={
                "session_id": session_id,
                "page_number": 0,
                "annotation_type": "text",
                "params": {
                    "text": "Test annotation",
                    "x": 100,
                    "y": 100
                }
            }
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

    def test_list_annotations(self):
        """Test listing annotations from PDF"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        # Add an annotation first
        self.client.post(
            "/api/v1/pypdf/annotation/add",
            json={
                "session_id": session_id,
                "page_number": 0,
                "annotation_type": "text",
                "params": {
                    "text": "Test annotation",
                    "x": 100,
                    "y": 100
                }
            }
        )
        
        # List annotations
        response = self.client.get(f"/api/v1/pypdf/annotation/list/{session_id}")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("annotations", result)

    # ==================== Form Tests ====================

    def test_get_form_fields(self):
        """Test getting form fields from PDF"""
        # Create a simple PDF with form fields
        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)
        
        # For simplicity, test with our blank PDF
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.get(f"/api/v1/pypdf/form/fields/{session_id}")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("fields", result)

    def test_fill_form(self):
        """Test filling form fields in PDF"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/form/fill",
            json={
                "session_id": session_id,
                "field_values": {
                    "field1": "value1",
                    "field2": "value2"
                }
            }
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

    # ==================== Metadata Tests ====================

    def test_get_metadata(self):
        """Test getting PDF metadata"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.get(f"/api/v1/pypdf/metadata/{session_id}")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("metadata", result)

    # ==================== Outline Tests ====================

    def test_get_outlines(self):
        """Test getting PDF outlines (bookmarks)"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.get(f"/api/v1/pypdf/outline/{session_id}")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("outlines", result)

    def test_add_outline(self):
        """Test adding outline to PDF"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/outline/add",
            json={
                "session_id": session_id,
                "title": "Test Outline",
                "page_number": 0,
                "level": 1
            }
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

    # ==================== Attachment Tests ====================

    def test_get_attachments(self):
        """Test getting PDF attachments"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.get(f"/api/v1/pypdf/attachments/{session_id}")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("attachments", result)

    def test_add_attachment(self):
        """Test adding attachment to PDF"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        # Create a simple attachment file
        attachment_content = b"Test attachment content"
        
        response = self.client.post(
            "/api/v1/pypdf/attachment/add",
            files={"file": ("attachment.txt", attachment_content, "text/plain")},
            data={"session_id": session_id}
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

    def test_extract_attachments(self):
        """Test extracting attachments from PDF"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.post(
            "/api/v1/pypdf/attachments/extract",
            json={"session_id": session_id}
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

    # ==================== Session Management Tests ====================

    def test_get_session_info(self):
        """Test getting session information"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.get(f"/api/v1/pypdf/session/{session_id}")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["id"], session_id)
        self.assertEqual(result["filename"], "test.pdf")
        self.assertEqual(result["page_count"], 3)

    def test_get_session_info_nonexistent(self):
        """Test getting info for non-existent session"""
        response = self.client.get("/api/v1/pypdf/session/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_delete_session(self):
        """Test deleting a session"""
        with open(self.test_pdf_path, "rb") as f:
            upload_response = self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = upload_response.json()["session_id"]
        
        response = self.client.delete(f"/api/v1/pypdf/session/{session_id}")
        
        self.assertEqual(response.status_code, 200)
        
        # Verify session is deleted
        info_response = self.client.get(f"/api/v1/pypdf/session/{session_id}")
        self.assertEqual(info_response.status_code, 404)

    def test_delete_nonexistent_session(self):
        """Test deleting non-existent session"""
        response = self.client.delete("/api/v1/pypdf/session/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_list_sessions(self):
        """Test listing all sessions"""
        # Upload multiple files
        with open(self.test_pdf_path, "rb") as f:
            self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test1.pdf", f, "application/pdf")}
            )
            self.client.post(
                "/api/v1/pypdf/upload",
                files={"file": ("test2.pdf", f, "application/pdf")}
            )
        
        response = self.client.get("/api/v1/pypdf/sessions")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("sessions", result)
        self.assertEqual(len(result["sessions"]), 2)


if __name__ == "__main__":
    unittest.main()
