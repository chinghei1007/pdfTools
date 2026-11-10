from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from apis import all_routers

app = FastAPI()

for router in all_routers:
    app.include_router(router)


FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@app.get("/{path:path}", include_in_schema=False)
def serve_frontend(path: str):
    # Unknown API URLs and missing assets should never return the SPA HTML.
    if path == "api" or path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")

    root = FRONTEND_DIST.resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise HTTPException(status_code=404, detail="Not found")
    if target.is_file():
        return FileResponse(target)
    if path.startswith("assets/"):
        raise HTTPException(status_code=404, detail="Not found")

    index = root / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=503, detail="Frontend build is not available")
    return FileResponse(index)
