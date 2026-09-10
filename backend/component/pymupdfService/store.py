"""Local preview persistence, independent of the existing application's schema."""
import os
import sqlite3
import uuid
from pathlib import Path
from contextlib import contextmanager

ROOT = Path(os.environ.get("PYMUPDF_DATA_DIR", Path(__file__).parent / ".data")).resolve()


@contextmanager
def connect():
    ROOT.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(ROOT / "service.db")
    db.row_factory = sqlite3.Row
    db.executescript('''
      CREATE TABLE IF NOT EXISTS files (
        id TEXT PRIMARY KEY, owner TEXT NOT NULL, name TEXT NOT NULL,
        media_type TEXT NOT NULL, size INTEGER NOT NULL, pages INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP);
      CREATE TABLE IF NOT EXISTS previews (
        file_id TEXT NOT NULL, page INTEGER NOT NULL, width INTEGER NOT NULL,
        height INTEGER NOT NULL, PRIMARY KEY(file_id,page));
    ''')
    try:
        with db:
            yield db
    finally:
        db.close()


def save(owner, name, data, media_type, pages=0):
    id = uuid.uuid4().hex
    ROOT.mkdir(parents=True, exist_ok=True)
    path = ROOT / id
    path.write_bytes(data)
    try:
        with connect() as db:
            db.execute("INSERT INTO files(id,owner,name,media_type,size,pages) VALUES(?,?,?,?,?,?)", (id, owner, name, media_type, len(data), pages))
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return dict(id=id, name=name, mediaType=media_type, size=len(data), pages=pages, persisted=True)


def get(id, owner):
    with connect() as db:
        row = db.execute("SELECT * FROM files WHERE id=? AND owner=?", (id, owner)).fetchone()
    if not row: raise KeyError("File not found in this browser session.")
    return dict(row), ROOT / row["id"]
