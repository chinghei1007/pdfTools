"""Unit tests for pymupdfAPI.py - PyMuPDF-specific API endpoints"""
import tempfile
import unittest
from pathlib import Path

import pymupdf
from fastapi.testclient import TestClient

from component.pymupdfService import store
from expose.main import app


class PymupdfAPITest(unittest.TestCase):
    """Test cases for PyMuPDF API endpoints"""

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
        
        # Establish pymupdf session
        self.client.get("/api/v1/pymupdf/tools", headers=self.headers)

    def tearDown(self):
        """Clean up test fixtures"""
        self.client.close()
        store.ROOT = self.previous_root
        self.temp.cleanup()

    # ==================== Tools Endpoint Tests ====================

    def test_get_tools(self):
        """Test retrieving PyMuPDF tools"""
        # First establish session
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        response = self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        self.assertEqual(response.status_code, 200)
        tools = response.json()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)
        
        # Check tool structure
        for tool in tools:
            self.assertIn("id", tool)
            self.assertIn("label", tool)

    def test_get_catalog(self):
        """Test retrieving PyMuPDF library catalog"""
        response = self.client.get("/api/v1/pymupdf/catalog")
        self.assertEqual(response.status_code, 200)
        catalog = response.json()
        self.assertIsInstance(catalog, dict)
        self.assertGreater(len(catalog), 0)

    def test_get_pypdf_tools_from_pymupdf(self):
        """Test retrieving PyPDF tools from PyMuPDF endpoint"""
        # First establish session
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        response = self.client.get("/api/v1/pymupdf/pypdf/tools")
        self.assertEqual(response.status_code, 200)
        tools = response.json()
        self.assertIsInstance(tools, list)

    def test_get_checklist(self):
        """Test retrieving PyMuPDF checklist"""
        response = self.client.get("/api/v1/pymupdf/pypdf/checklist")
        self.assertEqual(response.status_code, 200)
        checklist = response.json()
        self.assertIsInstance(checklist, list)

    # ==================== File Upload Tests ====================

    def test_upload_valid_pdf(self):
        """Test uploading a valid PDF file to PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("id", result)
        self.assertIn("name", result)
        self.assertEqual(result["name"], "test.pdf")
        self.assertEqual(result["media_type"], "application/pdf")

    def test_upload_png_file(self):
        """Test uploading a PNG file to PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        # Create a simple PNG
        with pymupdf.open() as doc:
            doc.new_page()
            pixmap = doc[0].get_pixmap()
            png_bytes = pixmap.tobytes("png")
        
        response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.png", png_bytes, "image/png")},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["media_type"], "image/png")

    def test_upload_invalid_file_type(self):
        """Test uploading an unsupported file type to PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.txt", b"plain text", "text/plain")},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 415)

    def test_upload_without_session(self):
        """Test uploading without session to PyMuPDF fails"""
        response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 401)

    # ==================== File Download Tests ====================

    def test_download_file(self):
        """Test downloading an uploaded file from PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Download the file
        download_response = self.client.get(f"/api/v1/pymupdf/files/{file_id}/download")
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response.content, self.pdf)

    def test_download_nonexistent_file(self):
        """Test downloading a non-existent file from PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        response = self.client.get("/api/v1/pymupdf/files/nonexistent/download")
        self.assertEqual(response.status_code, 404)

    # ==================== Preview Tests ====================

    def test_make_preview(self):
        """Test generating a page preview in PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Generate preview
        preview_response = self.client.post(
            f"/api/v1/pymupdf/files/{file_id}/preview",
            json={"page": 1, "password": ""},
            headers=self.headers,
        )
        
        self.assertEqual(preview_response.status_code, 200)
        preview_data = preview_response.json()
        self.assertIn("url", preview_data)
        self.assertIn("width", preview_data)
        self.assertIn("height", preview_data)

    def test_get_preview(self):
        """Test retrieving a generated preview from PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Generate preview
        preview_response = self.client.post(
            f"/api/v1/pymupdf/files/{file_id}/preview",
            json={"page": 1, "password": ""},
            headers=self.headers,
        )
        preview_url = preview_response.json()["url"]
        
        # Get the preview
        get_response = self.client.get(preview_url)
        self.assertEqual(get_response.status_code, 200)
        self.assertTrue(get_response.content.startswith(b"\x89PNG"))

    def test_get_preview_without_generating(self):
        """Test getting preview without generating it first from PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Try to get preview without generating it
        response = self.client.get(f"/api/v1/pymupdf/files/{file_id}/preview?page=1")
        self.assertEqual(response.status_code, 404)

    # ==================== Operations Tests ====================

    def test_run_pymupdf_operation(self):
        """Test running a PyMuPDF operation"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Run select operation (reorder pages)
        response = self.client.post(
            "/api/v1/pymupdf/operations/select",
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

    def test_run_pypdf_operation_from_pymupdf(self):
        """Test running a PyPDF operation from PyMuPDF endpoint"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Run select operation
        response = self.client.post(
            "/api/v1/pymupdf/pypdf/operations/select",
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

    def test_run_unknown_operation(self):
        """Test running unknown operation in PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        response = self.client.post(
            "/api/v1/pymupdf/operations/unknown",
            json={"file_ids": [], "options": {}},
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 404)

    def test_run_operation_without_mutation_header(self):
        """Test running operation without mutation header in PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        response = self.client.post(
            "/api/v1/pymupdf/operations/select",
            json={"file_ids": [], "options": {}},
        )
        
        self.assertEqual(response.status_code, 403)

    def test_run_operation_with_invalid_options(self):
        """Test running operation with invalid options in PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Invalid page selection
        response = self.client.post(
            "/api/v1/pymupdf/operations/select",
            json={
                "file_ids": [file_id],
                "options": {"pages": "0"}  # Invalid page number
            },
            headers=self.headers,
        )
        
        self.assertEqual(response.status_code, 422)

    # ==================== Session Isolation Tests ====================

    def test_session_isolation_for_files(self):
        """Test that file access is isolated by session in PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Create second session and try to access first user's file
        with TestClient(app) as other_client:
            other_client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
            response = other_client.get(f"/api/v1/pymupdf/files/{file_id}/download")
            self.assertEqual(response.status_code, 404)

    def test_session_isolation_for_previews(self):
        """Test that preview access is isolated by session in PyMuPDF"""
        self.client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
        
        # Upload a file
        upload_response = self.client.post(
            "/api/v1/pymupdf/files",
            files={"file": ("test.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        file_id = upload_response.json()["id"]
        
        # Generate preview
        preview_response = self.client.post(
            f"/api/v1/pymupdf/files/{file_id}/preview",
            json={"page": 1, "password": ""},
            headers=self.headers,
        )
        preview_url = preview_response.json()["url"]
        
        # Create second session and try to access first user's preview
        with TestClient(app) as other_client:
            other_client.get("/api/v1/pymupdf/tools", headers={"x-toolkit-request": "1"})
            response = other_client.get(preview_url)
            self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
