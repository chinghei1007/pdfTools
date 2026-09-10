"""Run with uvicorn component.pymupdfService.app:app --app-dir backend."""
from fastapi import FastAPI
from apis.pymupdfAPI import router

app = FastAPI(title="PyMuPDF local workbench", description="Local development service; not a public authenticated deployment.")
app.include_router(router)
