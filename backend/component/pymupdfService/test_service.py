import os
import tempfile
import unittest
from pathlib import Path
import pymupdf
from fastapi.testclient import TestClient
from component.pymupdfService.app import app
from component.pymupdfService import store
from component.pymupdfService.catalog import TOOLS


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = store.ROOT
        store.ROOT = Path(self.temp.name)
        self.client = TestClient(app)
        self.client.get('/api/v1/pymupdf/tools')
        self.headers = {'x-toolkit-request': '1'}
        with pymupdf.open() as doc:
            for text in ['First Sample text', 'Second page']:
                doc.new_page().insert_text((40, 70), text)
            self.pdf = doc.tobytes()
        self.id = self.upload(self.pdf, 'test.pdf')['id']

    def tearDown(self):
        self.client.close()
        store.ROOT = self.root
        self.temp.cleanup()

    def upload(self, data, name):
        response = self.client.post('/api/v1/pymupdf/files', files={'file': (name, data)}, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def run_tool(self, id, file_ids=None, options=None):
        return self.client.post(f'/api/v1/pymupdf/operations/{id}', json={'file_ids': file_ids or [self.id], 'options': options or {}}, headers=self.headers)

    def test_every_menu_operation_and_outputs(self):
        with pymupdf.open(stream=self.pdf, filetype='pdf') as doc:
            image = self.upload(doc[0].get_pixmap().tobytes('png'), 'image.png')['id']
        for tool in TOOLS:
            with self.subTest(tool=tool['id']):
                options = {'password': 'example-password'} if tool['id'] == 'encrypt' else {}
                response = self.run_tool(tool['id'], [image] if tool['id'] == 'image-to-pdf' else None, options)
                self.assertEqual(response.status_code, 200, response.text)
                output = self.client.get(response.json()['downloadUrl'])
                self.assertEqual(output.status_code, 200)
                self.assertGreater(len(output.content), 0)

    def test_preview_cache_and_session_isolation(self):
        url = f'/api/v1/pymupdf/files/{self.id}/preview'
        first = self.client.post(url, json={}, headers=self.headers)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertFalse(first.json()['cached'])
        self.assertTrue(self.client.post(url, json={}, headers=self.headers).json()['cached'])
        self.assertTrue(self.client.get(first.json()['url']).content.startswith(b'\x89PNG'))
        with TestClient(app) as other:
            other.get('/api/v1/pymupdf/tools')
            self.assertEqual(other.get(first.json()['url']).status_code, 404)

    def test_reorder_and_validation(self):
        response = self.run_tool('select', options={'pages': '2,1'})
        data = self.client.get(response.json()['downloadUrl']).content
        with pymupdf.open(stream=data, filetype='pdf') as doc:
            self.assertIn('Second', doc[0].get_text())
        self.assertEqual(self.run_tool('render', options={'format': 'exe'}).status_code, 422)
        self.assertEqual(self.run_tool('select', options={'pages': '0'}).status_code, 422)
        self.assertEqual(self.run_tool('metadata', options={'path': 'outside'}).status_code, 422)
        bad = self.client.post('/api/v1/pymupdf/files', files={'file': ('fake.pdf', b'not a PDF')}, headers=self.headers)
        self.assertEqual(bad.status_code, 415)

    def test_redaction_and_encryption_change_document_content(self):
        response = self.run_tool('redact', options={'pages': '1', 'rect': '30,30,250,100'})
        with pymupdf.open(stream=self.client.get(response.json()['downloadUrl']).content, filetype='pdf') as doc:
            self.assertNotIn('First', doc[0].get_text())
            self.assertIn('Second', doc[1].get_text())
        response = self.run_tool('encrypt', options={'password': 'example-password'})
        with pymupdf.open(stream=self.client.get(response.json()['downloadUrl']).content, filetype='pdf') as doc:
            self.assertTrue(doc.needs_pass)
            self.assertTrue(doc.authenticate('example-password'))
            self.assertIn('First', doc[0].get_text())

    def test_app_watermark_is_detected_and_removed_exactly(self):
        added = self.run_tool('watermark', options={'pages': '1', 'text': 'PRIVATE'})
        self.assertEqual(added.status_code, 200, added.text)
        marked_id = added.json()['id']
        detected = self.run_tool('remove-watermark', [marked_id], {'pages': '1', 'mode': 'detect'})
        self.assertEqual(detected.status_code, 200, detected.text)
        self.assertIn(b'app-managed', self.client.get(detected.json()['downloadUrl']).content)
        removed = self.run_tool('remove-watermark', [marked_id], {'pages': '1', 'mode': 'remove-app'})
        self.assertEqual(removed.status_code, 200, removed.text)
        with pymupdf.open(stream=self.client.get(removed.json()['downloadUrl']).content, filetype='pdf') as document:
            self.assertEqual(list(document[0].annots() or []), [])


if __name__ == '__main__': unittest.main()
