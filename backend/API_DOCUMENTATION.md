# Dual-engine PDF Toolkit API

The production application uses one FastAPI process and one shared, owner-isolated
SQLite/file store. The browser is identified by the HttpOnly, SameSite=Strict
`pdf_toolkit_client` cookie. Its lifetime rolls forward for one year whenever the
SPA bootstraps or loads a catalog.

## Public API

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/v1/bootstrap` | Establish ownership and return the two engine descriptors. |
| GET | `/api/v1/{engine}/tools` | Return the declarative catalog for `pypdf` or `pymupdf`. |
| POST | `/api/v1/files` | Upload an owned PDF, PNG, JPEG, or HTML file. |
| POST | `/api/v1/files/{id}/preview` | Render and cache an owned page preview through PyMuPDF. |
| GET | `/api/v1/files/{id}/preview` | Return the cached private PNG preview. |
| GET | `/api/v1/files/{id}/download` | Download an owned input or output file. |
| POST | `/api/v1/{engine}/operations/{toolId}` | Execute a catalog operation and persist its job result. |
| GET | `/api/v1/history` | List newest-first jobs with filters and cursor pagination. |
| GET | `/api/v1/history/{jobId}` | Restore sanitized options and ordered input/output metadata. |

Operations accept JSON containing `fileIds` and `options`. Successful responses
contain `jobId`, `status`, `message`, and ordered `outputs`. A failed operation is
also persisted and returns a safe error response. Option keys containing
`password`, `secret`, or `token` are removed before persistence and never returned
by History.

History supports `engine`, `tool`, `status`, `limit` (maximum 50), and the opaque
`cursor` from the preceding page. Removed files remain visible with
`available: false` and no active download.

## Frontend routes

| Route | Purpose |
| --- | --- |
| `/` | Redirects to `/pypdf/render`. |
| `/api-check` | Runs production API self-checks for one operation per engine and records those jobs in History. |
| `/:engineId/:toolId` | Loads the main workspace for `pypdf` and `pymupdf` tools (for example `/pypdf/render`). |
| `*` | Redirects unknown paths to `/pypdf/render`. |

## Persistence and compatibility

The shared store owns `files`, `previews`, `jobs`, and `job_files`. Files and jobs
do not expire automatically. Legacy operation-specific pypdf routes remain as
compatibility wrappers, but the SPA uses only the public routes above. The former
`/api/v1/pymupdf/pypdf/*` workbench surface is not mounted in production.

## Limits and validation

- 20 MB per file and at most 10 inputs per operation.
- PDF documents contain 1–1000 pages.
- At most 30 selected pages per synchronous operation.
- Rendering accepts 36–300 DPI and at most 12 megapixels per page.
- Catalog fields are declarative and may use constraints, choices, and `visibleWhen`.
- Catalogs never expose callbacks, executable instructions, or filesystem paths.

Run the server from `backend`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn expose.main:app --reload --port 8001
```

Interactive API documentation is at `http://localhost:8001/docs`.
