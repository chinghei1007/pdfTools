"""Run with uvicorn component.pymupdfService.app:app --app-dir backend."""
from fastapi import FastAPI
from apis.pymupdfAPI import router
from apis.toolkitAPI import router as toolkit_router

app = FastAPI(title="PyMuPDF local workbench", description="Local development service; not a public authenticated deployment.")
app.include_router(router)
app.include_router(toolkit_router)
