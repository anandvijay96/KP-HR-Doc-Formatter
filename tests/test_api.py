import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
import io

from app.main import app
from app.models.schemas import JobStatus, TemplateInfo, ExtractedData, ContactInfo

client = TestClient(app)

class TestAPI:
    """Test cases for API endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "HR Resume Formatter API"
        assert data["version"] == "1.0.0"
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "hr-resume-formatter"
    
    @patch('app.services.job_manager.JobManager')
    @patch('app.services.document_processor.DocumentProcessor')
    def test_upload_single_resume(self, mock_doc_processor, mock_job_manager):
        """Test single resume upload"""
        # Mock services
        mock_processor = Mock()
        mock_processor.save_uploaded_file = AsyncMock(return_value="test_file.docx")
        mock_doc_processor.return_value = mock_processor
        
        mock_manager = Mock()
        mock_manager.create_job = AsyncMock(return_value="test-job-id")
        mock_manager.start_background_job = AsyncMock()
        mock_job_manager.return_value = mock_manager
        
        # Create test file
        file_content = b"fake docx content"
        files = {"file": ("test_resume.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        data = {"template_id": "default"}
        
        response = client.post("/api/v1/upload/single", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["filename"] == "test_resume.docx"
        assert result["job_id"] == "test-job-id"
        assert "uploaded successfully" in result["message"]
    
    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type"""
        file_content = b"fake content"
        files = {"file": ("test_resume.txt", io.BytesIO(file_content), "text/plain")}
        data = {"template_id": "default"}
        
        response = client.post("/api/v1/upload/single", files=files, data=data)
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    
    @patch('app.services.job_manager.JobManager')
    def test_get_job_status(self, mock_job_manager):
        """Test job status endpoint"""
        # Mock job manager
        mock_manager = Mock()
        mock_manager.get_job_status = AsyncMock(return_value={
            "job_id": "test-job-id",
            "status": "completed",
            "original_filename": "test.docx",
            "processing_time": 5.2
        })
        mock_job_manager.return_value = mock_manager
        
        response = client.get("/api/v1/jobs/test-job-id/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert data["status"] == "completed"
    
    @patch('app.services.job_manager.JobManager')
    def test_get_job_status_not_found(self, mock_job_manager):
        """Test job status for non-existent job"""
        mock_manager = Mock()
        mock_manager.get_job_status = AsyncMock(return_value={"error": "Job not found"})
        mock_job_manager.return_value = mock_manager
        
        response = client.get("/api/v1/jobs/nonexistent-job/status")
        
        assert response.status_code == 404
    
    @patch('app.services.template_engine.TemplateEngine')
    def test_list_templates(self, mock_template_engine):
        """Test templates listing endpoint"""
        mock_engine = Mock()
        mock_engine.list_templates.return_value = [
            TemplateInfo(
                id="default",
                name="Default Template",
                description="Standard template",
                version="1.0",
                fields=["contact_info", "experience"],
                created_at="2023-01-01T00:00:00",
                updated_at="2023-01-01T00:00:00"
            )
        ]
        mock_template_engine.return_value = mock_engine
        
        response = client.get("/api/v1/templates/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "default"
        assert data[0]["name"] == "Default Template"
    
    @patch('app.services.template_engine.TemplateEngine')
    def test_get_template(self, mock_template_engine):
        """Test get specific template endpoint"""
        mock_engine = Mock()
        mock_engine.get_template_info.return_value = TemplateInfo(
            id="default",
            name="Default Template",
            description="Standard template",
            version="1.0",
            fields=["contact_info", "experience"],
            created_at="2023-01-01T00:00:00",
            updated_at="2023-01-01T00:00:00"
        )
        mock_template_engine.return_value = mock_engine
        
        response = client.get("/api/v1/templates/default")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "default"
        assert data["name"] == "Default Template"
    
    @patch('app.services.template_engine.TemplateEngine')
    def test_get_template_not_found(self, mock_template_engine):
        """Test get non-existent template"""
        mock_engine = Mock()
        mock_engine.get_template_info.return_value = None
        mock_template_engine.return_value = mock_engine
        
        response = client.get("/api/v1/templates/nonexistent")
        
        assert response.status_code == 404
    
    @patch('app.services.template_engine.TemplateEngine')
    def test_template_preview(self, mock_template_engine):
        """Test template preview endpoint"""
        mock_engine = Mock()
        mock_engine.get_template_preview.return_value = {
            "template_id": "default",
            "structure": {
                "header": {"name": "{{contact_info.name}}"},
                "sections": [
                    {"title": "Experience", "content": "{{experience}}"}
                ]
            }
        }
        mock_template_engine.return_value = mock_engine
        
        response = client.get("/api/v1/templates/default/preview")
        
        assert response.status_code == 200
        data = response.json()
        assert data["template_id"] == "default"
        assert "structure" in data
    
    def test_batch_upload_too_many_files(self):
        """Test batch upload with too many files"""
        files = []
        for i in range(12):  # More than the limit of 10
            file_content = b"fake content"
            files.append(("files", (f"test_{i}.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")))
        
        data = {"template_id": "default"}
        
        response = client.post("/api/v1/upload/batch", files=files, data=data)
        
        assert response.status_code == 400
        assert "Maximum 10 files" in response.json()["detail"]
    
    @patch('app.services.job_manager.JobManager')
    def test_cancel_job(self, mock_job_manager):
        """Test job cancellation"""
        from app.models.schemas import ProcessingJob, JobStatus
        
        mock_job = ProcessingJob(
            job_id="test-job-id",
            status=JobStatus.PROCESSING,
            template_id="default",
            original_filename="test.docx"
        )
        
        mock_manager = Mock()
        mock_manager.get_job = AsyncMock(return_value=mock_job)
        mock_manager.update_job_status = AsyncMock(return_value=True)
        mock_manager.document_processor = Mock()
        mock_manager.document_processor.cleanup_file = Mock(return_value=True)
        mock_job_manager.return_value = mock_manager
        
        response = client.delete("/api/v1/jobs/test-job-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert "cancelled successfully" in data["message"]
    
    @patch('app.services.job_manager.JobManager')
    @patch('app.services.document_processor.DocumentProcessor')
    def test_upload_single_pdf(self, mock_doc_processor, mock_job_manager):
        """Test single PDF upload is accepted and processed via job manager"""
        # Mock services
        mock_processor = Mock()
        mock_processor.save_uploaded_file = AsyncMock(return_value="test_file.pdf")
        mock_doc_processor.return_value = mock_processor
        
        mock_manager = Mock()
        mock_manager.create_job = AsyncMock(return_value="test-job-id")
        mock_manager.start_background_job = AsyncMock()
        mock_job_manager.return_value = mock_manager
        
        # Create test file
        file_content = b"%PDF-1.4 minimal"
        files = {"file": ("test_resume.pdf", io.BytesIO(file_content), "application/pdf")}
        # Do not pass template_id so default is used (ezest-updated)
        response = client.post("/api/v1/upload/single", files=files)
        
        assert response.status_code == 200
        result = response.json()
        assert result["filename"] == "test_resume.pdf"
        assert result["job_id"] == "test-job-id"
        assert "uploaded successfully" in result["message"]
    
    @patch('app.services.job_manager.JobManager')
    def test_cancel_completed_job(self, mock_job_manager):
        """Test cancelling already completed job"""
        from app.models.schemas import ProcessingJob, JobStatus
        
        mock_job = ProcessingJob(
            job_id="test-job-id",
            status=JobStatus.COMPLETED,
            template_id="default",
            original_filename="test.docx"
        )
        
        mock_manager = Mock()
        mock_manager.get_job = AsyncMock(return_value=mock_job)
        mock_job_manager.return_value = mock_manager
        
        response = client.delete("/api/v1/jobs/test-job-id")
        
        assert response.status_code == 400
        assert "Cannot cancel completed job" in response.json()["detail"]
