from fastapi import APIRouter
from app.api.v1 import upload, jobs, templates, download

api_router = APIRouter()

# Include all API route modules
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(download.router, prefix="/download", tags=["download"])
