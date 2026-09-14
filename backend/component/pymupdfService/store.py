"""Local preview persistence, independent of the existing application's schema."""
import base64
import json
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
        height INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(file_id,page));
      CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, owner TEXT NOT NULL, engine TEXT NOT NULL,
        tool_id TEXT NOT NULL, status TEXT NOT NULL, options_json TEXT NOT NULL,
        error_code TEXT, error_message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP, started_at TEXT,
        finished_at TEXT);
      CREATE TABLE IF NOT EXISTS job_files (
        job_id TEXT NOT NULL, file_id TEXT NOT NULL, role TEXT NOT NULL,
        position INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(job_id,file_id,role));
      CREATE INDEX IF NOT EXISTS jobs_owner_created
        ON jobs(owner,created_at DESC,id DESC);
      CREATE INDEX IF NOT EXISTS job_files_job ON job_files(job_id,role,position);
    ''')
    # Existing preview databases predate created_at. Keep the migration additive.
    columns = {row[1] for row in db.execute("PRAGMA table_info(previews)")}
    if "created_at" not in columns:
        db.execute("ALTER TABLE previews ADD COLUMN created_at TEXT")
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


def create_job(owner, engine, tool_id, options, file_ids):
    job_id = uuid.uuid4().hex
    with connect() as db:
        db.execute(
            """INSERT INTO jobs(id,owner,engine,tool_id,status,options_json,started_at)
               VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)""",
            (job_id, owner, engine, tool_id, "running", json.dumps(options)),
        )
        for position, file_id in enumerate(file_ids):
            db.execute(
                "INSERT INTO job_files(job_id,file_id,role,position) VALUES(?,?,?,?)",
                (job_id, file_id, "input", position),
            )
    return job_id


def finish_job(job_id, output_ids):
    with connect() as db:
        for position, file_id in enumerate(output_ids):
            db.execute(
                "INSERT INTO job_files(job_id,file_id,role,position) VALUES(?,?,?,?)",
                (job_id, file_id, "output", position),
            )
        db.execute(
            "UPDATE jobs SET status='completed',finished_at=CURRENT_TIMESTAMP WHERE id=?",
            (job_id,),
        )


def fail_job(job_id, code, message):
    with connect() as db:
        db.execute(
            """UPDATE jobs SET status='failed',error_code=?,error_message=?,
               finished_at=CURRENT_TIMESTAMP WHERE id=?""",
            (code, message, job_id),
        )


def _file_payload(row):
    if not row or row["id"] is None:
        return None
    item = dict(row)
    item.pop("role", None)
    item["mediaType"] = item.pop("media_type")
    item["available"] = (ROOT / item["id"]).exists()
    item["downloadUrl"] = f"/api/v1/files/{item['id']}/download"
    return item


def _job_payload(db, row, include_files=True):
    item = dict(row)
    item.pop("owner", None)
    item["toolId"] = item.pop("tool_id")
    item["createdAt"] = item.pop("created_at")
    item["startedAt"] = item.pop("started_at")
    item["finishedAt"] = item.pop("finished_at")
    item["errorCode"] = item.pop("error_code")
    item["errorMessage"] = item.pop("error_message")
    item["options"] = json.loads(item.pop("options_json") or "{}")
    if include_files:
        links = db.execute(
            """SELECT jf.role,f.* FROM job_files jf
               LEFT JOIN files f ON f.id=jf.file_id
               WHERE jf.job_id=? ORDER BY jf.role,jf.position""",
            (item["id"],),
        ).fetchall()
        item["inputs"] = [_file_payload(link) for link in links if link["role"] == "input"]
        item["outputs"] = [_file_payload(link) for link in links if link["role"] == "output"]
    return item


def history(owner, engine=None, tool_id=None, status=None, limit=50, cursor=None):
    offset = 0
    if cursor:
        try:
            offset = int(base64.urlsafe_b64decode(cursor + "===").decode())
        except (ValueError, UnicodeDecodeError):
            raise ValueError("Invalid history cursor.") from None
    clauses, values = ["owner=?"], [owner]
    for column, value in (("engine", engine), ("tool_id", tool_id), ("status", status)):
        if value:
            clauses.append(f"{column}=?")
            values.append(value)
    limit = max(1, min(int(limit), 50))
    with connect() as db:
        rows = db.execute(
            f"""SELECT * FROM jobs WHERE {' AND '.join(clauses)}
                 ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?""",
            (*values, limit + 1, offset),
        ).fetchall()
        entries = [_job_payload(db, row) for row in rows[:limit]]
    next_cursor = None
    if len(rows) > limit:
        next_cursor = base64.urlsafe_b64encode(str(offset + limit).encode()).decode().rstrip("=")
    return entries, next_cursor


def get_job(job_id, owner):
    with connect() as db:
        row = db.execute("SELECT * FROM jobs WHERE id=? AND owner=?", (job_id, owner)).fetchone()
        if not row:
            raise KeyError("History record not found in this browser.")
        return _job_payload(db, row)
