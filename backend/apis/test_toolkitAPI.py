"""Unit tests for toolkitAPI.py - Main PDF Toolkit API endpoints"""
import tempfile
import unittest
from pathlib import Path

import pymupdf
from fastapi.testclient import TestClient

from component.pymupdfService import store
from expose.main import app


class ToolkitAPITest(unittest.TestCase):
    """Test cases for the main toolkit API endpoints"""

    def setUp(self):
        """Set up test fixtures with isolated storage"""
        self.temp = tempfile.TemporaryDirectory()
        self.previous_root = store.ROOT
        store.ROOT = Path(self.temp.name)
        self.client = TestClient(app)
        self.headers = {"x-toolkit-request": "1"}
        
        # Create a test PDF
        with pymupdf.open() as doc:
            doc.new_page().insert_text((40, 70), "First page")
            doc.new_page().insert_text((40, 70), "Second page")
            self.pdf = doc.tobytes()

    def tearDown(self):
        """Clean up test fixtures"""
        self.client.close()
        store.ROOT = self.previous_root
        self.temp.cleanup()

    # ==================== Bootstrap Endpoint Tests ====================

    def test_bootstrap_creates_new_session(self):
        """Test that bootstrap creates a new session cookie"""
        response = self.client.get("/api/v1/bootstrap")
        self.assertEqual(response.status_code, 200)
        self.assertIn("pdf_toolkit_client", response.cookies)
        self.assertIn("engines", response.json())
        engines = response.json()["engines"]
        self.assertEqual(len(engines), 2)
        engine_ids = [e["id"] for e in engines]
        self.assertIn("pypdf", engine_ids)
        self.assertIn("pymupdf", engine_ids)

    def test_bootstrap_uses_existing_session(self):
        """Test that bootstrap reuses existing session"""
        # First call creates session
        first_response = self.client.get("/api/v1/bootstrap")
        first_cookie = first_response.cookies.get("pdf_toolkit_client")
        
        # Second call with same client should use existing session
        second_response = self.client.get("/api/v1/bootstrap")
        second_cookie = second_response.cookies.get("pdf_toolkit_client")
        
        self.assertEqual(first_cookie, second_cookie)
        self.assertEqual(second_response.status_code, 200)

    # ==================== Tools Endpoint Tests ====================

    def test_get_pypdf_tools(self):
        """Test retrieving pypdf engine tools"""
        # First establish session
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.get("/api/v1/pypdf/tools")
        self.assertEqual(response.status_code, 200)
        tools = response.json()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)
        
        # Check tool structure
        for tool in tools:
            self.assertIn("id", tool)
            self.assertIn("label", tool)

    def test_get_pymupdf_tools(self):
        """Test retrieving pymupdf engine tools"""
        # First establish session
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.get("/api/v1/pymupdf/tools")
        self.assertEqual(response.status_code, 200)
        tools = response.json()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)

    def test_get_unknown_engine_tools(self):
        """Test retrieving tools for unknown engine returns 404"""
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.get("/api/v1/unknown/tools")
        self.assertEqual(response.status_code, 404)

    def test_tools_without_session(self):
        """Test that tools endpoint works without session (returns pypdf tools)"""
        # No session established - pypdf/tools returns tools for both engines
        response = self.client.get("/api/v1/pypdf/tools")
        self.assertEqual(response.status_code, 200)
        tools = response.json()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)

    # ==================== File Upload Tests ====================

    def test_upload_valid_pdf(self):
        """Test uploading a valid PDF file"""
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("id", result)
        self.assertIn("name", result)
        self.assertEqual(result.get("name"), "test.pdf")
        self.assertEqual(result.get("mediaType"), "application/pdf")
        self.assertEqual(result.get("pages"), 2)

    def test_upload_png_file(self):
        """Test uploading a PNG file"""
        self.client.get("/api/v1/bootstrap")
        
        # Create a simple PNG
        with pymupdf.open() as doc:
            doc.new_page()
            pixmap = doc[0].get_pixmap()
            png_bytes = pixmap.tobytes("png")
        
        response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.png", png_bytes, "image/png")},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.get("mediaType"), "image/png")
        self.assertGreaterEqual(result.get("pages", 0), 0)

    def test_upload_html_file(self):
        """Test uploading an HTML file"""
        self.client.get("/api/v1/bootstrap")
        
        html_content = b"<html><body><h1>Test</h1></body></html>"
        
        response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.html", html_content, "text/html")},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.get("mediaType"), "text/html")
        self.assertGreaterEqual(result.get("pages", 0), 0)

    def test_upload_invalid_file_type(self):
        """Test uploading an unsupported file type"""
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.txt", b"plain text", "text/plain")},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 415)

    def test_upload_empty_file(self):
        """Test uploading an empty file"""
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.post(
            "/api/v1/files",
            files={"file": ("empty.pdf", b"", "application/pdf")},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 413)

    def test_upload_file_too_large(self):
        """Test uploading a file exceeding size limit"""
        self.client.get("/api/v1/bootstrap")
        
        # Create a file larger than 20MB
        large_data = b"A" * (20 * 1024 * 1024 + 1)
        
        response = self.client.post(
            "/api/v1/files",
            files={"file": ("large.pdf", large_data, "application/pdf")},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 413)

    def test_upload_without_mutation_header(self):
        """Test uploading without mutation header fails"""
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
        )
        
        self.assertEqual(response.status_code, 403)

    def test_upload_without_session(self):
        """Test uploading without session fails"""
        response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 401)

    def test_upload_password_protected_pdf(self):
        """Test uploading a password-protected PDF without password"""
        self.client.get("/api/v1/bootstrap")
        
        # Create password-protected PDF using pypdf
        from pypdf import PdfWriter
        import io
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.encrypt("secret")
        
        buf = io.BytesIO()
        writer.write(buf)
        protected_pdf = buf.getvalue()
        
        response = self.client.post(
            "/api/v1/files",
            files={"file": ("protected.pdf", protected_pdf, "application/pdf")},
            headers=self.headers,
            data={"password": ""},  # No password provided
        )
        
        self.assertEqual(response.status_code, 422)

    def test_upload_password_protected_pdf_with_password(self):
        """Test uploading a password-protected PDF with correct password"""
        self.client.get("/api/v1/bootstrap")
        
        # Create password-protected PDF using pypdf
        from pypdf import PdfWriter
        import io
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.encrypt("secret")
        
        buf = io.BytesIO()
        writer.write(buf)
        protected_pdf = buf.getvalue()
        
        response = self.client.post(
            "/api/v1/files",
            files={"file": ("protected.pdf", protected_pdf, "application/pdf")},
            headers=self.headers,
            data={"password": "secret"},
        )
        
        self.assertEqual(response.status_code, 200)

    # ==================== File Download Tests ====================

    def test_download_file(self):
        """Test downloading an uploaded file"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Download the file
        download_response = self.client.get(f"/api/v1/files/{file_id}/download")
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response.content, self.pdf)
        self.assertEqual(download_response.headers["content-type"], "application/pdf")

    def test_download_nonexistent_file(self):
        """Test downloading a non-existent file"""
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.get("/api/v1/files/nonexistent/download")
        self.assertEqual(response.status_code, 404)

    def test_download_another_owners_file(self):
        """Test that users cannot download each other's files"""
        # Create first session and upload
        self.client.get("/api/v1/bootstrap")
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Create second session and try to download first user's file
        with TestClient(app) as other_client:
            other_client.get("/api/v1/bootstrap")
            response = other_client.get(f"/api/v1/files/{file_id}/download")
            self.assertEqual(response.status_code, 404)

    # ==================== Preview Tests ====================

    def test_make_preview(self):
        """Test generating a page preview"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Generate preview
        preview_response = self.client.post(
            f"/api/v1/files/{file_id}/preview",
            json={"page": 1, "password": ""},
            headers=self.headers,
        )
        
        self.assertEqual(preview_response.status_code, 200)
        preview_data = preview_response.json()
        self.assertIn("url", preview_data)
        self.assertIn("width", preview_data)
        self.assertIn("height", preview_data)
        self.assertFalse(preview_data["cached"])

    def test_make_preview_caching(self):
        """Test that preview is cached on subsequent requests"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # First preview request
        first_response = self.client.post(
            f"/api/v1/files/{file_id}/preview",
            json={"page": 1, "password": ""},
            headers=self.headers,
        )
        
        # Second preview request should be cached
        second_response = self.client.post(
            f"/api/v1/files/{file_id}/preview",
            json={"page": 1, "password": ""},
            headers=self.headers,
        )
        
        self.assertTrue(first_response.json()["cached"] == False)
        self.assertTrue(second_response.json()["cached"] == True)

    def test_get_preview(self):
        """Test retrieving a generated preview"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Generate preview
        preview_response = self.client.post(
            f"/api/v1/files/{file_id}/preview",
            json={"page": 1, "password": ""},
            headers=self.headers,
        )
        preview_url = preview_response.json()["url"]
        
        # Get the preview
        get_response = self.client.get(preview_url)
        self.assertEqual(get_response.status_code, 200)
        self.assertTrue(get_response.content.startswith(b"\x89PNG"))

    def test_get_preview_without_generating(self):
        """Test getting preview without generating it first"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Try to get preview without generating it
        response = self.client.get(f"/api/v1/files/{file_id}/preview?page=1")
        self.assertEqual(response.status_code, 404)

    def test_preview_non_pdf_file(self):
        """Test that preview fails for non-PDF files"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a PNG file
        with pymupdf.open() as doc:
            doc.new_page()
            pixmap = doc[0].get_pixmap()
            png_bytes = pixmap.tobytes("png")
        
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.png", png_bytes, "image/png")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Try to generate preview for PNG
        response = self.client.post(
            f"/api/v1/files/{file_id}/preview",
            json={"page": 1, "password": ""},
            headers=self.headers,
        )
        
        # PNG files have 0 pages, so preview should fail
        self.assertIn(response.status_code, [415, 422])

    # ==================== Operations Tests ====================

    def test_run_pypdf_operation(self):
        """Test running a pypdf operation"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Run select operation (reorder pages)
        response = self.client.post(
            "/api/v1/pypdf/operations/select",
            json={
                "file_ids": [file_id],
                "options": {"pages": "2,1"}
            },
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("job", result)
        self.assertIn("outputs", result)
        self.assertEqual(len(result["outputs"]), 1)
        self.assertTrue(result["outputs"][0]["available"])
        self.assertIn("downloadUrl", result["outputs"][0])

    def test_run_pymupdf_operation(self):
        """Test running a pymupdf operation"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Run render operation
        response = self.client.post(
            "/api/v1/pymupdf/operations/render",
            json={
                "file_ids": [file_id],
                "options": {"pages": "1", "format": "png", "dpi": 72}
            },
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("job", result)
        self.assertIn("outputs", result)

    def test_run_unknown_engine_operation(self):
        """Test running operation on unknown engine"""
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.post(
            "/api/v1/unknown/operations/select",
            json={"file_ids": [], "options": {}},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 404)

    def test_run_unknown_operation(self):
        """Test running unknown operation"""
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.post(
            "/api/v1/pypdf/operations/unknown",
            json={"file_ids": [], "options": {}},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 404)

    def test_run_operation_without_mutation_header(self):
        """Test running operation without mutation header"""
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.post(
            "/api/v1/pypdf/operations/select",
            json={"file_ids": [], "options": {}},
        )
        
        self.assertEqual(response.status_code, 403)

    def test_run_operation_with_invalid_options(self):
        """Test running operation with invalid options"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Invalid page selection
        response = self.client.post(
            "/api/v1/pypdf/operations/select",
            json={
                "file_ids": [file_id],
                "options": {"pages": "0"}  # Invalid page number
            },
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 422)

    def test_secret_redaction_in_job_options(self):
        """Test that secrets are redacted from job options"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Run encrypt operation with password
        response = self.client.post(
            "/api/v1/pypdf/operations/encrypt",
            json={
                "file_ids": [file_id],
                "options": {"password": "my-secret-password"}
            },
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 200)
        job_id = response.json()["job"]["id"]
        
        # Get job details
        job_response = self.client.get(f"/api/v1/history/{job_id}")
        job_data = job_response.json()
        
        # Password should be redacted
        self.assertNotIn("password", job_data["options"])

    # ==================== History Tests ====================

    def test_history_list(self):
        """Test listing job history"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Run an operation
        self.client.post(
            "/api/v1/pypdf/operations/select",
            json={"file_ids": [file_id], "options": {"pages": "1"}},
            headers=self.headers,
        )
        
        # Get history
        response = self.client.get("/api/v1/history?limit=50")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("entries", result)
        self.assertGreater(len(result["entries"]), 0)

    def test_history_filter_by_engine(self):
        """Test filtering history by engine"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Run pypdf operation
        self.client.post(
            "/api/v1/pypdf/operations/select",
            json={"file_ids": [file_id], "options": {"pages": "1"}},
            headers=self.headers,
        )
        
        # Run pymupdf operation
        self.client.post(
            "/api/v1/pymupdf/operations/render",
            json={"file_ids": [file_id], "options": {"pages": "1", "format": "png", "dpi": 72}},
            headers=self.headers,
        )
        
        # Filter by pypdf engine
        response = self.client.get("/api/v1/history?engine=pypdf&limit=50")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        for entry in result["entries"]:
            self.assertEqual(entry["engine"], "pypdf")

    def test_history_filter_by_status(self):
        """Test filtering history by status"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Run a successful operation
        self.client.post(
            "/api/v1/pypdf/operations/select",
            json={"file_ids": [file_id], "options": {"pages": "1"}},
            headers=self.headers,
        )
        
        # Run a failed operation
        self.client.post(
            "/api/v1/pypdf/operations/select",
            json={"file_ids": [file_id], "options": {"pages": "0"}},
            headers=self.headers,
        )
        
        # Filter by failed status
        response = self.client.get("/api/v1/history?status=failed&limit=50")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        for entry in result["entries"]:
            self.assertEqual(entry["status"], "failed")

    def test_history_detail(self):
        """Test getting job detail from history"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Run an operation
        operation_response = self.client.post(
            "/api/v1/pypdf/operations/select",
            json={"file_ids": [file_id], "options": {"pages": "1"}},
            headers=self.headers,
        )
        job_id = operation_response.json()["job"]["id"]
        
        # Get job detail
        response = self.client.get(f"/api/v1/history/{job_id}")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["id"], job_id)
        self.assertIn("toolId", result)
        self.assertIn("engine", result)
        self.assertIn("status", result)

    def test_history_detail_nonexistent(self):
        """Test getting detail for non-existent job"""
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.get("/api/v1/history/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_history_isolation(self):
        """Test that history is isolated by owner"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload and run operation in first session
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        self.client.post(
            "/api/v1/pypdf/operations/select",
            json={"file_ids": [file_id], "options": {"pages": "1"}},
            headers=self.headers,
        )
        
        # Second session should have empty history
        with TestClient(app) as other_client:
            other_client.get("/api/v1/bootstrap")
            response = other_client.get("/api/v1/history?limit=50")
            self.assertEqual(response.json()["entries"], [])

    # ==================== Pagination Tests ====================

    def test_history_pagination(self):
        """Test history pagination with cursor"""
        self.client.get("/api/v1/bootstrap")
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Run multiple operations
        for i in range(5):
            self.client.post(
                "/api/v1/pypdf/operations/select",
                json={"file_ids": [file_id], "options": {"pages": f"{i+1}"}},
                headers=self.headers,
            )
        
        # Get first page
        response = self.client.get("/api/v1/history?limit=3")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(len(result["entries"]), 3)
        self.assertIsNotNone(result.get("nextCursor"))

    def test_history_invalid_cursor(self):
        """Test history with invalid cursor"""
        self.client.get("/api/v1/bootstrap")
        
        response = self.client.get("/api/v1/history?cursor=invalid")
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
