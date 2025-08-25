from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse
from typing import Dict, Any

from app.models.schemas import JobResponse, JobStatus
from app.services.job_manager import JobManager

router = APIRouter()
job_manager = JobManager()

@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str = Path(..., description="Job ID to check status")
) -> Dict[str, Any]:
    """Get the status of a processing job"""
    
    try:
        job_status = await job_manager.get_job_status(job_id)
        
        if "error" in job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving job status: {str(e)}")

@router.get("/{job_id}/result")
async def get_job_result(
    job_id: str = Path(..., description="Job ID to get result")
) -> Dict[str, Any]:
    """Get the result of a completed processing job"""
    
    try:
        job = await job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status == JobStatus.PENDING or job.status == JobStatus.PROCESSING:
            raise HTTPException(status_code=202, detail="Job still processing")
        
        if job.status == JobStatus.FAILED:
            raise HTTPException(status_code=400, detail=f"Job failed: {job.error_message}")
        
        # Return extracted data for completed jobs
        result = {
            "job_id": job.job_id,
            "status": job.status,
            "original_filename": job.original_filename,
            "output_filename": job.output_filename,
            "extracted_data": job.extracted_data.model_dump() if job.extracted_data else None,
            "processing_time": job.processing_time
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving job result: {str(e)}")

@router.delete("/{job_id}")
async def cancel_job(
    job_id: str = Path(..., description="Job ID to cancel")
) -> Dict[str, str]:
    """Cancel a processing job"""
    
    try:
        job = await job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status == JobStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Cannot cancel completed job")
        
        if job.status == JobStatus.FAILED:
            raise HTTPException(status_code=400, detail="Cannot cancel failed job")
        
        # Update job status to failed (cancellation)
        await job_manager.update_job_status(
            job_id, 
            JobStatus.FAILED, 
            error_message="Job cancelled by user"
        )
        
        # Clean up uploaded file
        if job.original_filename:
            job_manager.document_processor.cleanup_file(job.original_filename)
        
        return {"message": "Job cancelled successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling job: {str(e)}")
