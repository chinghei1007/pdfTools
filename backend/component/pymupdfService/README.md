# PyMuPDF workbench V1

## Run

From the repository root:

```powershell
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python.exe -m uvicorn component.pymupdfService.app:app --app-dir backend --host 127.0.0.1 --port 8001
npm --prefix frontend run dev
```

Open http://127.0.0.1:5173/preview_pymupdf_V1 (the requested spelling `/preview_pymypdf_V1` also works). Interactive API documentation: http://127.0.0.1:8001/docs.

This standalone entry avoids the existing pypdf service's incompatible `Underline` import. The existing combined app's pypdf dependency issue is not repaired here. The new router is also registered in `apis.all_routers` for integration once that is resolved.

## API contract

Prefix `/api/v1/pymupdf`. First GET `/tools` to establish a local browser-session cookie. Mutations require `X-Toolkit-Request: 1`. Vite proxies only this prefix to port 8001.

- GET `/tools`: executable operation catalogue and field definitions; UI navigation is generated from this.
- GET `/catalog`: read-only inventory of installed PyMuPDF public callables and public class members. Inventory does not imply an executable HTTP adapter.
- POST `/files`: multipart `file`, optional `password`. Validates content signature and opens the document. Returns `{id,name,mediaType,size,pages,persisted:true}` after SQLite commit.
- POST `/files/{id}/preview`: `{page:1,password:""}`. Render/cache a thumbnail with longest side at most 600px. Returns `{url,width,height,cached}`.
- GET `/files/{id}/preview?page=1`: session-scoped cached PNG.
- POST `/operations/{tool}`: `{file_ids:[id],options:{...},passwords:{[id]:password}}`. Synchronous bounded operation, returns stored result and downloadUrl. Multiple outputs are zipped. Empty extraction returns an empty ZIP.
- GET `/files/{id}/download`: session-scoped attachment response, never a client-provided storage path.

Page numbers are 1-based. All options are allowlisted per operation. Comma-separated pages and inclusive ranges (1-3,5,4) allow duplicates; blank means all, limited to 30 selected pages. Source uploads are immutable. The UI exposes a thumbnail reorder grid for documents with at most 30 pages, and page-number input for other selections.

## Implemented menu

- Convert: image to PDF; page rendering PNG/JPEG; SVG.
- Extract: text/HTML/XHTML/XML/JSON; embedded images; tables; annotation/link/form/vector information.
- Inspect: metadata; bookmarks; embedded attachments; text search.
- Pages: merge; select/reorder; split; rotate; crop.
- Edit: optimize; text watermark; highlight text; rectangle redaction; sticky note; title/author; flatten annotations/forms.
- Security: AES-256 encryption; unlocked output after successful input authentication.

These 28 adapters are NOT every PyMuPDF function. The catalogue includes the broader reference surface. Not implemented as HTTP tools: OCR/Tesseract, Story/HTML input rendering, arbitrary form/link/annotation editing, fonts/geometry constructors, low-level xref editing, journalling, optional-content management, and Pro/4LLM-specific APIs. Multipage TIFF is not advertised because the current renderer exports PNG/JPEG. No arbitrary Python method invocation is exposed.

## Persistence and limits

`store.py` creates its own SQLite files/previews tables and generated file paths under ignored `.data/`. Set PYMUPDF_DATA_DIR to relocate. This is separate from existing database/schema.sql. Previews refer to source file IDs and page numbers. Output files are stored in files; full job/audit history is not implemented. Passwords remain in request/browser memory and are not stored or logged.

This is a **local development service**, with opaque browser-session ownership, not account authentication. Keep it loopback-only. Files persist until manually managed; there is no retention scheduler yet. Before public deployment, add real authentication, quotas, cleanup, isolated worker processes, timeouts and total-output bounds. Upload limit 20 MB; at most 10 input files, 1000 source pages, 30 selected pages, 300 DPI and 12 megapixels per rendered page. Processing is serialized in one process because PyMuPDF is not thread-safe; this is not a durable job queue. Complex files can still consume significant processing time.

The thumbnail cost is one cached render per file/page and private PNG storage/download. No API usage fee is charged by this local service. Infrastructure and PyMuPDF's AGPL/commercial licensing are separate considerations. See https://pymupdf.readthedocs.io/en/latest/ for current library documentation.

## Test

```powershell
cd backend
.venv/Scripts/python.exe -m pip install httpx
.venv/Scripts/python.exe -m unittest component.pymupdfService.test_service -v
```

Tests generate synthetic PDFs, exercise every menu operation, verify preview caching/session isolation, inspect reordered output, and reject invalid options/content. Fixtures and SQLite are isolated in temporary storage.

## pypdf workbench

`/previewpyPDF_V1` and `/previewV1` now open the connected pypdf workbench. Preview aliases for both engines are case-insensitive (including optional .html and trailing slash). The old component demo is still available by its direct examples/previewV1.html path.

GET `/api/v1/pymupdf/pypdf/tools` lists pypdf tools and the explicitly labelled PyMuPDF-assisted conversions. POST `/api/v1/pymupdf/pypdf/operations/{tool}` uses the same request shape and shared immutable uploads as the PyMuPDF workbench. GET `/api/v1/pymupdf/pypdf/checklist` returns the 56-function audit from the supplied reference. See `frontend/src/components/pypdf/CHECKLIST.md` for test steps and missing/partial functionality. This adapter does not import or fix the legacy pypdfServices package.
