import tempfile
import unittest
from pathlib import Path

import pymupdf
from fastapi.testclient import TestClient

from component.pymupdfService import store
from expose.main import app


class ToolkitApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_root = store.ROOT
        store.ROOT = Path(self.temp.name)
        self.client = TestClient(app)
        bootstrap = self.client.get("/api/v1/bootstrap")
        self.assertEqual(bootstrap.status_code, 200, bootstrap.text)
        self.headers = {"x-toolkit-request": "1"}
        with pymupdf.open() as document:
            document.new_page().insert_text((40, 70), "First page")
            document.new_page().insert_text((40, 70), "Second page")
            self.pdf = document.tobytes()
        response = self.client.post(
            "/api/v1/files",
            files={"file": ("source.pdf", self.pdf, "application/pdf")},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.file_id = response.json()["id"]

    def tearDown(self):
        self.client.close()
        store.ROOT = self.previous_root
        self.temp.cleanup()

    def run_tool(self, engine, tool, options=None, file_ids=None):
        return self.client.post(
            f"/api/v1/{engine}/operations/{tool}",
            json={"file_ids": file_ids if file_ids is not None else [self.file_id], "options": options or {}},
            headers=self.headers,
        )

    def test_cross_engine_history_and_restore(self):
        pypdf = self.run_tool("pypdf", "select", {"pages": "2,1"})
        self.assertEqual(pypdf.status_code, 200, pypdf.text)
        pymupdf_result = self.run_tool("pymupdf", "render", {"pages": "1", "format": "png", "dpi": 72})
        self.assertEqual(pymupdf_result.status_code, 200, pymupdf_result.text)
        history = self.client.get("/api/v1/history?limit=50").json()
        self.assertEqual({entry["engine"] for entry in history["entries"]}, {"pypdf", "pymupdf"})
        detail = self.client.get(f"/api/v1/history/{pypdf.json()['job']['id']}").json()
        self.assertEqual(detail["toolId"], "select")
        self.assertEqual(detail["options"], {"pages": "2,1"})
        self.assertTrue(detail["outputs"][0]["available"])
        self.assertNotIn("owner", detail)

    def test_secret_redaction_failed_jobs_and_isolation(self):
        encrypted = self.run_tool("pypdf", "encrypt", {"password": "example-password"})
        self.assertEqual(encrypted.status_code, 200, encrypted.text)
        detail = self.client.get(f"/api/v1/history/{encrypted.json()['job']['id']}").json()
        self.assertNotIn("password", detail["options"])
        failure = self.run_tool("pypdf", "select", {"pages": "0"})
        self.assertEqual(failure.status_code, 422)
        failed = self.client.get("/api/v1/history?status=failed").json()["entries"]
        self.assertEqual(failed[0]["status"], "failed")
        with TestClient(app) as other:
            other.get("/api/v1/bootstrap")
            self.assertEqual(other.get("/api/v1/history").json()["entries"], [])
            self.assertEqual(other.get(detail["outputs"][0]["downloadUrl"]).status_code, 404)

    def test_html_file_to_pdf_and_checklist_completion(self):
        uploaded = self.client.post(
            "/api/v1/files",
            files={"file": ("page.html", b"<h1>Local HTML</h1>", "text/html")},
            headers=self.headers,
        )
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        rendered = self.run_tool("pymupdf", "html-to-pdf", file_ids=[uploaded.json()["id"]])
        self.assertEqual(rendered.status_code, 200, rendered.text)
        self.assertTrue(self.client.get(rendered.json()["outputs"][0]["downloadUrl"]).content.startswith(b"%PDF"))
        import json
        checklist = json.loads((Path(__file__).parent / "pypdf_checklist.json").read_text(encoding="utf-8"))
        self.assertEqual(sum(row["status"] == "Available" for row in checklist), 55)
        self.assertEqual(sum(row["status"] == "Assisted" for row in checklist), 1)
        text = json.dumps(checklist)
        for unsupported in ("Underline", "Squiggly", "StrikeOut"):
            self.assertNotIn(unsupported, text)


if __name__ == "__main__":
    unittest.main()
