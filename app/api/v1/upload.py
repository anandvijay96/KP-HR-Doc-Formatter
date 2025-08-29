from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import os

from app.core.config import settings
from app.models.schemas import UploadResponse, BatchUploadResponse
import app.services.document_processor as document_processor_module
import app.services.job_manager as job_manager_module

router = APIRouter()

# Dependency providers (simple factories). Tests can patch the classes these call.
def get_document_processor() -> document_processor_module.DocumentProcessor:
    return document_processor_module.DocumentProcessor()

def get_job_manager() -> job_manager_module.JobManager:
    return job_manager_module.JobManager()

@router.post("/single", response_model=UploadResponse)
async def upload_single_resume(
    file: UploadFile = File(...),
    template_id: str = Form(default="ezest-updated"),
    use_gemini: bool = Form(default=False),
    gemini_api_key: Optional[str] = Form(default=None),
    document_processor: document_processor_module.DocumentProcessor = Depends(get_document_processor),
    job_manager: job_manager_module.JobManager = Depends(get_job_manager),
):
    """Upload a single resume file for processing"""
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    # Robust allow: honor settings plus accept PDFs by MIME or extension
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        is_pdf = (file_extension == '.pdf') or (getattr(file, 'content_type', '') == 'application/pdf')
        if not is_pdf:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    try:
        # Save file
        unique_filename = await document_processor.save_uploaded_file(
            file_content, file.filename
        )
        
        # Create processing job (optionally with Gemini LLM)
        job_id = await job_manager.create_job(
            unique_filename,
            template_id,
            use_gemini=use_gemini,
            gemini_api_key=gemini_api_key,
        )
        
        # Start background processing
        await job_manager.start_background_job(job_id)
        
        return UploadResponse(
            filename=file.filename,
            file_size=len(file_content),
            job_id=job_id,
            message="File uploaded successfully. Processing started."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/batch", response_model=BatchUploadResponse)
async def upload_batch_resumes(
    files: List[UploadFile] = File(...),
    template_id: str = Form(default="ezest-updated"),
    use_gemini: bool = Form(default=False),
    gemini_api_key: Optional[str] = Form(default=None),
    document_processor: document_processor_module.DocumentProcessor = Depends(get_document_processor),
    job_manager: job_manager_module.JobManager = Depends(get_job_manager),
):
    """Upload multiple resume files for batch processing"""
    
    if len(files) > 10:  # Limit batch size
        raise HTTPException(status_code=400, detail="Maximum 10 files per batch")
    
    successful_uploads = 0
    failed_uploads = 0
    job_ids = []
    errors = []
    
    for file in files:
        try:
            if not file.filename:
                errors.append(f"Empty filename in batch")
                failed_uploads += 1
                continue
                
            file_extension = os.path.splitext(file.filename)[1].lower()
            is_pdf = (file_extension == '.pdf') or (getattr(file, 'content_type', '') == 'application/pdf')
            if file_extension not in settings.ALLOWED_EXTENSIONS and not is_pdf:
                errors.append(f"{file.filename}: Unsupported file type")
                failed_uploads += 1
                continue
            
            file_content = await file.read()
            if len(file_content) > settings.MAX_FILE_SIZE:
                errors.append(f"{file.filename}: File too large")
                failed_uploads += 1
                continue
            
            # Save file and create job
            unique_filename = await document_processor.save_uploaded_file(
                file_content, file.filename
            )
            job_id = await job_manager.create_job(
                unique_filename,
                template_id,
                use_gemini=use_gemini,
                gemini_api_key=gemini_api_key,
            )
            
            # Start background processing
            await job_manager.start_background_job(job_id)
            
            job_ids.append(job_id)
            successful_uploads += 1
            
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
            failed_uploads += 1
    
    return BatchUploadResponse(
        total_files=len(files),
        successful_uploads=successful_uploads,
        failed_uploads=failed_uploads,
        job_ids=job_ids,
        errors=errors
    )

@router.get("/_debug")
async def upload_debug():
    """Debug endpoint to verify server code version and allowed extensions."""
    return {
        "allowed_extensions": settings.ALLOWED_EXTENSIONS,
        "content": "upload_v2_pdf_allow",
    }
