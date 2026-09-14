"""Shared, browser-owned API used by the production dual-engine SPA."""
from __future__ import annotations

import re
import secrets
import threading
from pathlib import Path

import pymupdf
from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from component.pymupdfService import operations, store
from component.pymupdfService.catalog import TOOLS as PYMUPDF_TOOLS
from component.pymupdfService.pypdf_workbench import TOOLS as PYPDF_TOOLS
from component.pymupdfService.pypdf_workbench import process as process_pypdf


router = APIRouter(prefix="/api/v1", tags=["PDF Toolkit"])
lock = threading.Lock()
COOKIE = "pdf_toolkit_client"
COOKIE_MAX_AGE = 365 * 24 * 60 * 60
ENGINES = ({"id": "pypdf", "label": "pypdf"}, {"id": "pymupdf", "label": "PyMuPDF"})


def _owner(request: Request, response: Response | None = None) -> str:
    value = request.cookies.get(COOKIE, "")
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        if response is None:
            raise HTTPException(401, "Open the PDF Toolkit first.")
        value = secrets.token_hex(32)
    if response is not None:
        response.set_cookie(
            COOKIE,
            value,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="strict",
        )
    return value


def _mutation(request: Request) -> None:
    if request.headers.get("x-toolkit-request") != "1":
        raise HTTPException(403, "Missing application request header.")


def _file(file_id: str, owner: str):
    try:
        return store.get(file_id, owner)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from None


def _safe_options(value):
    if isinstance(value, dict):
        return {
            key: _safe_options(item)
            for key, item in value.items()
            if not any(secret in key.lower() for secret in ("password", "secret", "token", "credential"))
        }
    if isinstance(value, list):
        return [_safe_options(item) for item in value]
    return value


def _page_count(data: bytes, mime: str) -> int:
    if mime != "application/pdf":
        return 0
    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            return document.page_count
    except Exception:
        return 0


@router.get("/bootstrap")
def bootstrap(request: Request, response: Response):
    _owner(request, response)
    return {"engines": ENGINES}


@router.get("/{engine}/tools")
def tools(engine: str, request: Request, response: Response):
    _owner(request, response)
    if engine == "pypdf":
        return PYPDF_TOOLS
    if engine == "pymupdf":
        return PYMUPDF_TOOLS
    raise HTTPException(404, "Unknown PDF engine.")


@router.post("/files")
def upload(
    request: Request,
    file: UploadFile = File(...),
    password: str = Form(""),
):
    _mutation(request)
    owner = _owner(request)
    data = file.file.read(20 * 1024 * 1024 + 1)
    if not data or len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "Use a nonempty file under 20 MB.")
    lowered = (file.filename or "").lower()
    if data.startswith(b"%PDF-"):
        kind, mime = "pdf", "application/pdf"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        kind, mime = "png", "image/png"
    elif data.startswith(b"\xff\xd8\xff"):
        kind, mime = "jpeg", "image/jpeg"
    elif lowered.endswith((".html", ".htm")):
        kind, mime = "html", "text/html"
    else:
        raise HTTPException(415, "Only PDF, JPEG, PNG and HTML content is accepted.")
    pages = 0
    if kind != "html":
        try:
            with lock, pymupdf.open(stream=data, filetype=kind) as document:
                if document.needs_pass and not document.authenticate(password):
                    raise ValueError("A valid input password is required.")
                pages = document.page_count
                if not 0 < pages <= 1000:
                    raise ValueError("Use a document with 1–1000 pages.")
        except Exception as exc:
            raise HTTPException(422, f"Cannot open document: {type(exc).__name__}. Check the file and password.") from None
    return store.save(owner, file.filename or f"document.{kind}", data, mime, pages)


class PreviewBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page: int = Field(default=1, ge=1, le=1000)
    password: str = Field(default="", max_length=256)


@router.post("/files/{file_id}/preview")
def make_preview(file_id: str, body: PreviewBody, request: Request):
    _mutation(request)
    row, path = _file(file_id, _owner(request))
    if row["media_type"] != "application/pdf":
        raise HTTPException(415, "Only PDF files have generated page previews.")
    target = store.ROOT / f"{path.name}-p{body.page}.png"
    with lock:
        with store.connect() as db:
            cached = db.execute(
                "SELECT * FROM previews WHERE file_id=? AND page=?", (file_id, body.page)
            ).fetchone()
        if not cached or not target.exists():
            try:
                data, width, height = operations.preview(path, body.password, body.page)
            except Exception:
                raise HTTPException(422, "Preview failed. Check the page and password.") from None
            target.write_bytes(data)
            with store.connect() as db:
                db.execute(
                    "INSERT OR REPLACE INTO previews(file_id,page,width,height) VALUES(?,?,?,?)",
                    (file_id, body.page, width, height),
                )
        else:
            width, height = cached["width"], cached["height"]
    return {
        "url": f"/api/v1/files/{file_id}/preview?page={body.page}",
        "width": width,
        "height": height,
        "cached": bool(cached),
    }


@router.get("/files/{file_id}/preview")
def get_preview(file_id: str, request: Request, page: int = 1):
    _, path = _file(file_id, _owner(request))
    target = store.ROOT / f"{path.name}-p{page}.png"
    if not target.exists():
        raise HTTPException(404, "Generate the preview first.")
    return FileResponse(target, media_type="image/png", headers={"Cache-Control": "private, no-store"})


@router.get("/files/{file_id}/download")
def download(file_id: str, request: Request):
    row, path = _file(file_id, _owner(request))
    if not path.exists():
        raise HTTPException(404, "The output file is no longer available.")
    return FileResponse(
        path,
        media_type=row["media_type"],
        filename=row["name"],
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"},
    )


class RunBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_ids: list[str] = Field(default_factory=list, max_length=10)
    options: dict = Field(default_factory=dict)
    passwords: dict[str, str] = Field(default_factory=dict)


@router.post("/{engine}/operations/{tool_id}")
def run(engine: str, tool_id: str, body: RunBody, request: Request):
    _mutation(request)
    owner = _owner(request)
    catalog = PYPDF_TOOLS if engine == "pypdf" else PYMUPDF_TOOLS if engine == "pymupdf" else None
    if catalog is None:
        raise HTTPException(404, "Unknown PDF engine.")
    if not any(tool["id"] == tool_id for tool in catalog):
        raise HTTPException(404, "Unknown operation.")
    paths = [(file_id, _file(file_id, owner)[1]) for file_id in body.file_ids]
    safe_options = _safe_options(body.options)
    job_id = store.create_job(owner, engine, tool_id, safe_options, body.file_ids)
    try:
        with lock:
            processor = process_pypdf if engine == "pypdf" else operations.process
            name, data, mime = processor(tool_id, paths, body.options, body.passwords)
        output = store.save(owner, name, data, mime, _page_count(data, mime))
        output["downloadUrl"] = f"/api/v1/files/{output['id']}/download"
        output["available"] = True
        store.finish_job(job_id, [output["id"]])
        job = store.get_job(job_id, owner)
        return {"job": job, "outputs": [output]}
    except (ValueError, TypeError, OverflowError) as exc:
        message = str(exc) or "The document operation could not be completed."
        store.fail_job(job_id, "INVALID_OPERATION", message)
        raise HTTPException(422, message) from None
    except Exception:
        message = "The document operation failed. Check the input and settings."
        store.fail_job(job_id, "PROCESSING_FAILED", message)
        raise HTTPException(422, message) from None


@router.get("/history")
def history(
    request: Request,
    engine: str | None = None,
    tool_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
):
    try:
        entries, next_cursor = store.history(
            _owner(request), engine, tool_id, status, limit, cursor
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    return {"entries": entries, "nextCursor": next_cursor}


@router.get("/history/{job_id}")
def history_detail(job_id: str, request: Request):
    try:
        return store.get_job(job_id, _owner(request))
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from None
