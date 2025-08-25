from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import FileResponse
from pathlib import Path as PathLib
import os

from app.core.config import settings
from app.services.job_manager import JobManager
from app.models.schemas import JobStatus

router = APIRouter()
job_manager = JobManager()

@router.get("/{job_id}")
async def download_result(
    job_id: str = Path(..., description="Job ID to download result")
):
    """Download the processed resume file"""
    
    try:
        job = await job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Job not completed yet")
        
        if not job.output_filename:
            raise HTTPException(status_code=404, detail="Output file not found")
        
        output_path = PathLib(settings.OUTPUT_DIR) / job.output_filename
        
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Output file does not exist")
        
        return FileResponse(
            path=str(output_path),
            filename=job.output_filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@router.delete("/{job_id}")
async def cleanup_job_files(
    job_id: str = Path(..., description="Job ID to cleanup files")
):
    """Clean up job files after download"""
    
    try:
        job = await job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Clean up input file
        if job.original_filename:
            job_manager.document_processor.cleanup_file(job.original_filename)
        
        # Clean up output file
        if job.output_filename:
            output_path = PathLib(settings.OUTPUT_DIR) / job.output_filename
            if output_path.exists():
                output_path.unlink()
        
        return {"message": "Job files cleaned up successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up files: {str(e)}")
