from celery import current_task
import asyncio
import logging
from typing import Dict, Any

from app.services.celery_app import celery_app
from app.services.document_processor import DocumentProcessor
from app.services.template_engine import TemplateEngine
from app.services.job_manager import JobManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='app.services.celery_tasks.process_resume_task')
def process_resume_task(self, job_id: str, filename: str, template_id: str) -> Dict[str, Any]:
    """
    Celery task for processing resume files
    """
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Starting processing'})
        
        # Initialize services
        document_processor = DocumentProcessor()
        template_engine = TemplateEngine()
        
        logger.info(f"Starting processing for job {job_id}, file: {filename}")
        
        # Process document (extract data)
        self.update_state(state='PROGRESS', meta={'status': 'Extracting data'})
        
        # Since we're in a sync context, we need to handle async calls carefully
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            extracted_data = loop.run_until_complete(
                document_processor.process_document(filename)
            )
        finally:
            loop.close()
        
        logger.info(f"Data extraction completed for job {job_id}")
        
        # Apply template
        self.update_state(state='PROGRESS', meta={'status': 'Applying template'})
        
        output_filename = template_engine.apply_template(extracted_data, template_id)
        
        logger.info(f"Template application completed for job {job_id}, output: {output_filename}")
        
        # Clean up input file
        document_processor.cleanup_file(filename)
        
        return {
            'status': 'completed',
            'job_id': job_id,
            'output_filename': output_filename,
            'extracted_data': extracted_data.model_dump(),
            'confidence_score': extracted_data.confidence_score
        }
        
    except Exception as exc:
        logger.error(f"Task failed for job {job_id}: {str(exc)}")
        
        # Update task state to failure
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'failed',
                'error': str(exc),
                'job_id': job_id
            }
        )
        
        # Clean up input file on failure
        try:
            document_processor = DocumentProcessor()
            document_processor.cleanup_file(filename)
        except:
            pass
        
        raise exc

@celery_app.task(name='app.services.celery_tasks.cleanup_old_files')
def cleanup_old_files() -> Dict[str, Any]:
    """
    Periodic task to clean up old files
    """
    try:
        from pathlib import Path
        import time
        from app.core.config import settings
        
        logger.info("Starting cleanup of old files")
        
        # Clean up files older than 24 hours
        cutoff_time = time.time() - (24 * 60 * 60)  # 24 hours ago
        
        cleaned_files = 0
        
        # Clean upload directory
        upload_dir = Path(settings.UPLOAD_DIR)
        for file_path in upload_dir.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    cleaned_files += 1
                    logger.info(f"Cleaned up old upload file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to clean up {file_path.name}: {str(e)}")
        
        # Clean output directory
        output_dir = Path(settings.OUTPUT_DIR)
        for file_path in output_dir.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    cleaned_files += 1
                    logger.info(f"Cleaned up old output file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to clean up {file_path.name}: {str(e)}")
        
        logger.info(f"Cleanup completed. Removed {cleaned_files} files.")
        
        return {
            'status': 'completed',
            'files_cleaned': cleaned_files
        }
        
    except Exception as exc:
        logger.error(f"Cleanup task failed: {str(exc)}")
        raise exc

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'app.services.celery_tasks.cleanup_old_files',
        'schedule': 60.0 * 60.0 * 6,  # Every 6 hours
    },
}
