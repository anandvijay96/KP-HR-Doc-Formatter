# HR Resume Formatter

An AI-powered automation tool that converts candidate resumes from DOC/DOCX format into agency-specific templates, reducing manual processing time from 2-3 hours to under 10 minutes.

## Features

- **Document Processing**: Extract data from DOC/DOCX resume files
- **Template Management**: Support for multiple agency-specific templates
- **AI-Powered Extraction**: OCR and NLP for intelligent data parsing
- **Batch Processing**: Handle multiple resumes simultaneously
- **Web Interface**: React-based dashboard for easy file management
- **Quality Assurance**: Data validation and accuracy checks

## Tech Stack

- **Backend**: Python 3.10+, FastAPI
- **Document Processing**: python-docx, docxtpl, unoconv
- **AI/ML**: spaCy, Tesseract OCR, OpenCV
- **Task Queue**: Celery with Redis
- **Frontend**: React.js, TypeScript
- **Testing**: pytest
- **Containerization**: Docker, docker-compose

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start Redis server:
```bash
redis-server
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## Project Structure

```
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Core functionality
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   └── main.py           # FastAPI application
├── templates/            # Agency templates
├── tests/               # Test files
├── frontend/            # React application
└── docker-compose.yml   # Container orchestration
```

## Development Phases

- **Phase 1**: Core backend API and document processing ✅
- **Phase 2**: Document extraction engine with OCR/NLP
- **Phase 3**: Template management system
- **Phase 4**: Frontend React application
- **Phase 5**: Testing, deployment, and containerization

## Success Metrics

- 90% reduction in processing time (from 2-3 hours to <10 minutes)
- 95%+ data extraction accuracy
- Support for concurrent processing of up to 10 resumes
- 99.5% system uptime
