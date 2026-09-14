"""Mountable router for the local PyMuPDF workbench."""
import logging
import secrets
import threading
import re
from fastapi import APIRouter, Request, Response, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ConfigDict
from component.pymupdfService import store, operations
from component.pymupdfService.catalog import TOOLS, library_catalog

router = APIRouter(prefix="/api/v1/pymupdf", tags=["PyMuPDF"])
lock = threading.Lock()  # PyMuPDF must not run concurrently in different threads.
logger = logging.getLogger("uvicorn.error")


def owner(request, response=None):
    value = request.cookies.get("pymupdf_session", "")
    if re.fullmatch(r"[0-9a-f]{64}", value): return value
    if response is None: raise HTTPException(401, "Open the workbench first.")
    value = secrets.token_hex(32)
    response.set_cookie("pymupdf_session", value, httponly=True, samesite="strict")
    return value


def mutation(request):
    if request.headers.get("x-toolkit-request") != "1":
        raise HTTPException(403, "Missing application request header.")


def file_for(id, session):
    try: return store.get(id, session)
    except KeyError as exc: raise HTTPException(404, str(exc)) from None


@router.get("/tools")
def tools(request: Request, response: Response):
    owner(request, response)
    return TOOLS


@router.get("/catalog")
def catalog():
    return library_catalog()


@router.get('/pypdf/tools')
def pypdf_tools(request: Request, response: Response):
    from component.pymupdfService.pypdf_workbench import TOOLS as tools
    owner(request, response)
    return tools


@router.get('/pypdf/checklist')
def pypdf_checklist():
    import json
    from pathlib import Path
    return json.loads((Path(__file__).parent.parent / 'component/pymupdfService/pypdf_checklist.json').read_text(encoding='utf-8'))


@router.post("/files")
def upload(request: Request, file: UploadFile = File(...), password: str = Form("")):
    mutation(request)
    session = owner(request)
    data = file.file.read(20 * 1024 * 1024 + 1)
    if not data or len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "Use a nonempty file under 20 MB.")
    if data.startswith(b"%PDF-"): kind, mime = "pdf", "application/pdf"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"): kind, mime = "png", "image/png"
    elif data.startswith(b"\xff\xd8\xff"): kind, mime = "jpeg", "image/jpeg"
    else: raise HTTPException(415, "Only PDF, JPEG and PNG content is accepted.")
    import pymupdf
    try:
        with lock, pymupdf.open(stream=data, filetype=kind) as doc:
            if doc.needs_pass and not doc.authenticate(password): raise ValueError("A valid input password is required.")
            count = doc.page_count
            if not 0 < count <= 1000: raise ValueError("Use a document with 1–1000 pages.")
    except Exception as exc: raise HTTPException(422, f"Cannot open document: {type(exc).__name__}. Check the file and password.") from None
    result = store.save(session, file.filename or f"document.{kind}", data, mime, count)
    logger.info("pymupdf file.db_save.succeeded")
    return result


class PreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page: int = Field(default=1, ge=1, le=1000)
    password: str = Field(default="", max_length=256)


@router.post("/files/{id}/preview")
def make_preview(id: str, body: PreviewRequest, request: Request):
    mutation(request)
    _, path = file_for(id, owner(request))
    target = store.ROOT / f"{path.name}-p{body.page}.png"
    with lock:
        with store.connect() as db:
            cached = db.execute("SELECT * FROM previews WHERE file_id=? AND page=?", (id, body.page)).fetchone()
        if not cached or not target.exists():
            try: data, width, height = operations.preview(path, body.password, body.page)
            except Exception: raise HTTPException(422, "Preview failed. Check page number and password.") from None
            target.write_bytes(data)
            with store.connect() as db:
                db.execute(
                    "INSERT OR REPLACE INTO previews(file_id,page,width,height) VALUES(?,?,?,?)",
                    (id, body.page, width, height),
                )
        else: width, height = cached["width"], cached["height"]
    logger.info("pymupdf preview.ready")
    return dict(url=f"/api/v1/pymupdf/files/{id}/preview?page={body.page}", width=width, height=height, cached=bool(cached))


@router.get("/files/{id}/preview")
def get_preview(id: str, request: Request, page: int = 1):
    _, path = file_for(id, owner(request))
    target = store.ROOT / f"{path.name}-p{page}.png"
    if not target.exists(): raise HTTPException(404, "Generate preview first.")
    return FileResponse(target, media_type="image/png", headers={"Cache-Control": "private, no-store"})


@router.get("/files/{id}/download")
def download(id: str, request: Request):
    row, path = file_for(id, owner(request))
    return FileResponse(path, media_type=row["media_type"], filename=row["name"], headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"})


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_ids: list[str] = Field(min_length=1, max_length=10)
    options: dict[str, str | int] = Field(default_factory=dict)
    passwords: dict[str, str] = Field(default_factory=dict)


@router.post("/operations/{tool}")
def run(tool: str, body: RunRequest, request: Request):
    mutation(request)
    session = owner(request)
    paths = [(id, file_for(id, session)[1]) for id in body.file_ids]
    try:
        with lock:
            name, data, mime = operations.process(tool, paths, body.options, body.passwords)
    except (ValueError, TypeError, OverflowError) as exc: raise HTTPException(422, str(exc)) from None
    except Exception: raise HTTPException(422, "Document operation failed; check the input and settings.") from None
    result = store.save(session, name, data, mime)
    result["downloadUrl"] = f"/api/v1/pymupdf/files/{result['id']}/download"
    logger.info("pymupdf operation.succeeded")
    return result


@router.post('/pypdf/operations/{tool}')
def run_pypdf(tool: str, body: RunRequest, request: Request):
    from component.pymupdfService.pypdf_workbench import process
    mutation(request)
    session=owner(request)
    paths=[(id,file_for(id,session)[1]) for id in body.file_ids]
    try:
        with lock: name,data,mime=process(tool,paths,body.options,body.passwords)
    except (ValueError, TypeError, OverflowError) as exc: raise HTTPException(422,str(exc)) from None
    except Exception: raise HTTPException(422,'pypdf operation failed. Check document and settings.') from None
    result=store.save(session,name,data,mime)
    result['downloadUrl']=f"/api/v1/pymupdf/files/{result['id']}/download"
    return result
