import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Configure async test event loop
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = True
    return mock_redis

@pytest.fixture
def sample_extracted_data():
    """Sample extracted data for testing"""
    from app.models.schemas import ExtractedData, ContactInfo, Experience, Education
    
    return ExtractedData(
        contact_info=ContactInfo(
            name="John Doe",
            email="john.doe@email.com",
            phone="555-123-4567",
            address="123 Main St, City, State 12345"
        ),
        summary="Experienced software engineer with 5 years in web development",
        experience=[
            Experience(
                title="Senior Software Engineer",
                company="Tech Corp",
                start_date="2020-01",
                end_date="Present",
                description="Lead development of web applications",
                is_current=True
            ),
            Experience(
                title="Software Engineer",
                company="StartupXYZ",
                start_date="2018-06",
                end_date="2019-12",
                description="Developed REST APIs and frontend components",
                is_current=False
            )
        ],
        education=[
            Education(
                degree="Bachelor of Science in Computer Science",
                institution="University of Technology",
                graduation_date="2018-05"
            )
        ],
        skills=["Python", "JavaScript", "React", "FastAPI", "PostgreSQL"],
        confidence_score=0.85
    )
