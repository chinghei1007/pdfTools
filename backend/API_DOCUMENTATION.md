# PyPDF Services API - Implementation Summary

## Overview
This document summarizes the implementation of the PyPDF FastAPI backend with complete PDF processing capabilities, session management, preview generation, and database schema.

## Directory Structure
```
backend/
├── apis/
│   ├── __init__.py              # Exports all_routers list
│   └── pypdfAPI.py              # Complete FastAPI router with 27 endpoints
├── component/
│   ├── common/
│   │   ├── __init__.py          # Exports helper functions
│   │   └── pdf_helpers.py       # Shared validate_file_exists, ensure_output_dir
│   └── pypdfServices/
│       ├── annotations.py       # Annotation handling (kept pypdf.annotations imports)
│       ├── attachments.py       # File attachments
│       ├── basic.py             # Merge, split, encrypt, decrypt, rotate
│       ├── content.py           # Low-level content stream access
│       ├── formHandling.py      # Form field operations
│       ├── images.py            # Image extraction
│       ├── metadata.py          # PDF metadata
│       ├── outlines.py          # Bookmarks/outlines
│       ├── pages.py             # Page transformations
│       └── text.py              # Text extraction
├── database/
│   ├── schema.sql               # Complete SQLite schema (10 tables + 3 views)
│   └── pypdf.db                 # Initialized database
├── output/
│   ├── uploads/                 # Uploaded PDF files
│   ├── previews/                # Generated preview images
│   └── processed/               # Processed output files
└── expose/
    └── main.py                  # FastAPI application entry point
```

## API Endpoints (27 total)

### Upload/Download
- `POST /api/v1/pypdf/upload` - Upload PDF file (returns session_id)
- `GET /api/v1/pypdf/download/{session_id}` - Download processed PDF
- `GET /api/v1/pypdf/download/preview/{session_id}` - Download preview image
  - Query params: `page_number` (optional, defaults to 0, out-of-range handled), `size` (small/large)
- `GET /api/v1/pypdf/preview/all/{session_id}` - Generate all previews

### Text Extraction
- `POST /api/v1/pypdf/extract/text` - Extract text (modes: standard, layout, orientation)

### Image Extraction
- `POST /api/v1/pypdf/extract/images` - Extract embedded images

### Basic Operations
- `POST /api/v1/pypdf/merge` - Merge multiple PDFs
- `POST /api/v1/pypdf/split` - Split PDF (by ranges or single pages)
- `POST /api/v1/pypdf/rotate` - Rotate pages (90, 180, 270 degrees)
- `POST /api/v1/pypdf/encrypt` - Add password protection
- `POST /api/v1/pypdf/decrypt` - Remove password protection

### Page Operations
- `POST /api/v1/pypdf/page/scale` - Scale pages (factor or target size)
- `POST /api/v1/pypdf/page/crop` - Crop pages
- `POST /api/v1/pypdf/page/remove` - Remove specific pages

### Annotations
- `POST /api/v1/pypdf/annotation/add` - Add annotation (free_text, rectangle, ellipse, line, polygon, highlight, text, link, uri_link)
- `GET /api/v1/pypdf/annotation/list/{session_id}` - List annotations

### Form Handling
- `GET /api/v1/pypdf/form/fields/{session_id}` - Get form fields
- `POST /api/v1/pypdf/form/fill` - Fill form fields

### Metadata & Outlines
- `GET /api/v1/pypdf/metadata/{session_id}` - Get PDF metadata
- `GET /api/v1/pypdf/outline/{session_id}` - Get bookmarks/outlines
- `POST /api/v1/pypdf/outline/add` - Add bookmark

### Attachments
- `GET /api/v1/pypdf/attachments/{session_id}` - List attachments
- `POST /api/v1/pypdf/attachment/add` - Add attachment
- `POST /api/v1/pypdf/attachments/extract` - Extract attachments

### Session Management
- `GET /api/v1/pypdf/session/{session_id}` - Get session info
- `DELETE /api/v1/pypdf/session/{session_id}` - Delete session
- `GET /api/v1/pypdf/sessions` - List active sessions

## Key Features

### 1. Session-Based Processing
- Each upload creates a unique session_id (UUID)
- Sessions expire after 24 hours with automatic cleanup
- All operations reference session_id instead of file paths
- Output files tracked in session state

### 2. Preview Generation
- **Small previews**: Longest edge = 100px (ignoring aspect ratio)
- **Large previews**: High-resolution (300 DPI)
- Automatic page number validation:
  - No page_number → first page (index 0)
  - Negative → first page (index 0)
  - Out of range (≥ total) → last page
- Previews cached per session

### 3. File Upload/Download Flow
```
Frontend → POST /upload (multipart/form-data with PDF blob)
         ← Returns: {session_id, page_count, size_bytes}

Frontend → GET /download/preview/{session_id}?page_number=0&size=small
         ← Returns: PNG image (100px max dimension)

Frontend → POST /rotate (with session_id, degrees)
         ← Returns: {output_path, message}

Frontend → GET /download/{session_id}
         ← Returns: Processed PDF file
```

### 4. Database Schema (SQLite)

**Core Tables:**
- `users` - Account identity (id, username, email, password_hash, role, status, timestamps)
- `sessions` - Login sessions (token_hash, expires_at, revoked_at)
- `files` - File records (owner_id, storage_key, original_name, size_bytes, page_count, status)
- `jobs` - Processing jobs (tool_id, options_json, status, progress, error_code)
- `job_files` - Junction table (job_id, file_id, role[input/output], position)
- `audit_events` - Activity logging (actor_user_id, action, target_type, outcome)

**Authentication Tables:**
- `auth_challenges` - Email verification, password reset tokens
- `mfa_methods` - 2FA methods (TOTP, WebAuthn)
- `recovery_codes` - One-time recovery codes
- `external_identities` - Third-party auth (Telegram, Google, GitHub, Microsoft)

**Views:**
- `active_sessions` - Currently valid user sessions
- `job_summary` - Jobs with input/output file counts
- `user_file_stats` - User file statistics

## Usage Example

### cURL Examples

```bash
# 1. Upload PDF
curl -X POST "http://localhost:8000/api/v1/pypdf/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"

# Response: {"session_id": "abc123...", "page_count": 10, ...}

# 2. Get small preview of first page
curl "http://localhost:8000/api/v1/pypdf/download/preview/abc123?page_number=0&size=small" \
  --output preview.png

# 3. Get high-res preview of last page (page 9 out of range handled)
curl "http://localhost:8000/api/v1/pypdf/download/preview/abc123?page_number=999&size=large" \
  --output preview_hires.png

# 4. Rotate PDF
curl -X POST "http://localhost:8000/api/v1/pypdf/rotate" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc123", "degrees": 90}'

# 5. Download processed PDF
curl "http://localhost:8000/api/v1/pypdf/download/abc123" \
  --output rotated.pdf
```

### Frontend JavaScript Example

```javascript
// Upload PDF
const formData = new FormData();
formData.append('file', pdfBlob);

const uploadResponse = await fetch('/api/v1/pypdf/upload', {
  method: 'POST',
  body: formData
});
const { session_id } = await uploadResponse.json();

// Get preview
const previewUrl = `/api/v1/pypdf/download/preview/${session_id}?size=small`;
document.getElementById('preview').src = previewUrl;

// Process PDF
await fetch('/api/v1/pypdf/rotate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id, degrees: 90 })
});

// Download result
window.location.href = `/api/v1/pypdf/download/${session_id}`;
```

## Notes

1. **Helper Functions**: Isolated in `component/common/pdf_helpers.py` and imported by all service modules
2. **Annotations Import**: Kept `from pypdf.annotations import (...)` as requested (recently updated)
3. **Output Directory**: All files stored in `output/` subdirectories (uploads/, previews/, processed/)
4. **Session Cleanup**: Background task removes files after 1 hour
5. **Page Number Handling**: Out-of-range pages automatically clamped to valid range (0 or last page)
6. **Database**: SQLite schema ready for production use with proper indexes and foreign keys

## Next Steps

1. Start the FastAPI server: `uvicorn expose.main:app --reload`
2. Access API docs at: `http://localhost:8000/docs`
3. Integrate authentication middleware with database schema
4. Add Redis for session storage in production
5. Implement background job queue for long-running operations
