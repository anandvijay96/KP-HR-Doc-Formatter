from fastapi import APIRouter, HTTPException, Path, Depends
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path as PathLib
import os
import io
import zipfile
from typing import List, Optional

from app.core.config import settings
import app.services.job_manager as job_manager_module
from app.models.schemas import JobStatus

router = APIRouter()

def get_job_manager() -> job_manager_module.JobManager:
    return job_manager_module.JobManager()

@router.get("/{job_id}")
async def download_result(
    job_id: str = Path(..., description="Job ID to download result"),
    job_manager: job_manager_module.JobManager = Depends(get_job_manager),
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

@router.post("/batch")
async def download_batch(
    job_ids: List[str],
    job_manager: job_manager_module.JobManager = Depends(get_job_manager),
):
    """Download multiple completed job outputs as a single ZIP archive.

    Body JSON example: {"job_ids": ["id1", "id2", ...]}
    """
    try:
        if not job_ids:
            raise HTTPException(status_code=400, detail="No job_ids provided")

        zip_buffer = io.BytesIO()
        added_any = False

        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for jid in job_ids:
                job = await job_manager.get_job(jid)
                if not job:
                    continue
                if job.status != JobStatus.COMPLETED:
                    continue
                if not job.output_filename:
                    continue
                output_path = PathLib(settings.OUTPUT_DIR) / job.output_filename
                if not output_path.exists():
                    continue

                # Choose archive name: prefer output filename; otherwise, derive from original with .docx
                arcname = job.output_filename or "output.docx"
                if getattr(job, 'original_filename', None):
                    base = os.path.basename(str(job.original_filename))
                    # Force .docx since formatted outputs are DOCX
                    name, _ext = os.path.splitext(base)
                    arcname = f"formatted_{name}.docx"
                try:
                    zf.write(str(output_path), arcname=arcname)
                    added_any = True
                except Exception:
                    # Skip problematic files
                    continue

        if not added_any:
            raise HTTPException(status_code=400, detail="No completed outputs available to download")

        zip_buffer.seek(0)
        headers = {
            "Content-Disposition": "attachment; filename=formatted_batch.zip"
        }
        return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating ZIP: {str(e)}")

@router.delete("/{job_id}")
async def cleanup_job_files(
    job_id: str = Path(..., description="Job ID to cleanup files"),
    job_manager: job_manager_module.JobManager = Depends(get_job_manager),
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
