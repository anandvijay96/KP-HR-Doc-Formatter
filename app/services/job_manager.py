import uuid
import asyncio
from datetime import datetime
from typing import Dict, Optional
import json
import redis.asyncio as redis

from app.core.config import settings
from app.models.schemas import ProcessingJob, JobStatus, ExtractedData
from app.services.document_processor import DocumentProcessor
from app.services.template_engine import TemplateEngine
import logging

class JobManager:
    """Manages processing jobs and their status"""
    
    def __init__(self):
        self.redis_client = None
        self.document_processor = DocumentProcessor()
        self.template_engine = TemplateEngine()
        
    async def get_redis_client(self):
        """Get Redis client connection"""
        if not self.redis_client:
            self.redis_client = redis.from_url(settings.REDIS_URL)
        return self.redis_client
    
    async def create_job(self, filename: str, template_id: str, *, use_gemini: bool = False, gemini_api_key: Optional[str] = None) -> str:
        """Create a new processing job"""
        job_id = str(uuid.uuid4())
        
        job = ProcessingJob(
            job_id=job_id,
            status=JobStatus.PENDING,
            template_id=template_id,
            original_filename=filename,
            use_gemini=use_gemini,
            gemini_api_key=gemini_api_key
        )
        
        # Store job in Redis
        redis_client = await self.get_redis_client()
        await redis_client.setex(
            f"job:{job_id}",
            3600,  # 1 hour TTL
            job.model_dump_json()
        )
        
        return job_id
    
    async def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Get job by ID"""
        redis_client = await self.get_redis_client()
        job_data = await redis_client.get(f"job:{job_id}")
        
        if job_data:
            return ProcessingJob.model_validate_json(job_data)
        return None
    
    async def update_job_status(self, job_id: str, status: JobStatus, **kwargs):
        """Update job status and additional fields"""
        job = await self.get_job(job_id)
        if not job:
            return False
            
        job.status = status
        
        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        if status == JobStatus.COMPLETED or status == JobStatus.FAILED:
            job.completed_at = datetime.now()
            if job.created_at:
                job.processing_time = (job.completed_at - job.created_at).total_seconds()
        
        # Store updated job
        redis_client = await self.get_redis_client()
        await redis_client.setex(
            f"job:{job_id}",
            3600,
            job.model_dump_json()
        )
        
        return True
    
    async def process_job(self, job_id: str):
        """Process a job asynchronously"""
        try:
            # Update status to processing
            await self.update_job_status(job_id, JobStatus.PROCESSING)
            
            job = await self.get_job(job_id)
            if not job:
                return
            
            # Process the document
            extracted_data = await self.document_processor.process_document(
                job.original_filename,
                use_gemini=bool(getattr(job, 'use_gemini', False)),
                gemini_api_key=getattr(job, 'gemini_api_key', None)
            )
            
            # Apply template to generate formatted resume (with fallback on error)
            output_filename = None
            primary_error = None
            try:
                logging.info(f"Rendering with template_id='{job.template_id}'")
                output_filename = self.template_engine.apply_template(extracted_data, job.template_id)
            except Exception as e:
                primary_error = str(e)
                # Try fallbacks in order
                fallbacks = []
                for tid in ["ezest-updated-bullets", "ezest", "default"]:
                    if tid != job.template_id:
                        fallbacks.append(tid)
                for tid in fallbacks:
                    try:
                        output_filename = self.template_engine.apply_template(extracted_data, tid)
                        # Attach a warning about fallback
                        try:
                            w = self.template_engine.get_last_warnings() or []
                        except Exception:
                            w = []
                        w = [f"Primary template '{job.template_id}' failed: {primary_error}. Fallback '{tid}' used."] + w
                        await self.update_job_status(
                            job_id,
                            JobStatus.COMPLETED,
                            extracted_data=extracted_data,
                            output_filename=output_filename,
                            warnings=w
                        )
                        return
                    except Exception:
                        continue
                # If all fallbacks failed, raise the original error
                raise
            
            warnings = []
            try:
                warnings = self.template_engine.get_last_warnings()
            except Exception:
                warnings = []
            
            await self.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                extracted_data=extracted_data,
                output_filename=output_filename,
                warnings=warnings
            )
            
        except Exception as e:
            await self.update_job_status(
                job_id,
                JobStatus.FAILED,
                error_message=str(e)
            )
    
    async def start_background_job(self, job_id: str):
        """Start job processing in background"""
        asyncio.create_task(self.process_job(job_id))

    async def update_job_extracted_data(self, job_id: str, data: dict) -> bool:
        """Update the stored extracted_data for a job."""
        job = await self.get_job(job_id)
        if not job:
            return False
        try:
            # Merge: if job has existing extracted_data, update fields; else, validate from scratch
            if job.extracted_data:
                existing = job.extracted_data.model_dump()
                existing.update(data or {})
                job.extracted_data = ExtractedData(**existing)
            else:
                job.extracted_data = ExtractedData(**(data or {}))
            # Persist
            redis_client = await self.get_redis_client()
            await redis_client.setex(f"job:{job_id}", 3600, job.model_dump_json())
            return True
        except Exception as e:
            logging.error(f"Failed to update job extracted_data: {e}")
            return False

    async def regenerate_output(self, job_id: str) -> Optional[str]:
        """Re-render the document for a job using its current extracted_data and template_id."""
        job = await self.get_job(job_id)
        if not job or not job.extracted_data:
            return None
        try:
            logging.info(f"Regenerating output for job {job_id} with template_id='{job.template_id}'")
            output_filename = self.template_engine.apply_template(job.extracted_data, job.template_id)
            await self.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                extracted_data=job.extracted_data,
                output_filename=output_filename,
                warnings=self.template_engine.get_last_warnings()
            )
            return output_filename
        except Exception as e:
            logging.error(f"Regeneration failed: {e}")
            await self.update_job_status(job_id, JobStatus.FAILED, error_message=str(e))
            return None
    
    async def get_job_status(self, job_id: str) -> Dict:
        """Get job status information"""
        job = await self.get_job(job_id)
        if not job:
            return {"error": "Job not found"}
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "original_filename": job.original_filename,
            "output_filename": job.output_filename,
            "error_message": job.error_message,
            "warnings": job.warnings,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "processing_time": job.processing_time
        }
