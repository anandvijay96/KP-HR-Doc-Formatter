#!/bin/bash

# Development startup script for HR Resume Formatter

echo "Starting HR Resume Formatter in development mode..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Download spaCy model if not present
python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null || {
    echo "Downloading spaCy English model..."
    python -m spacy download en_core_web_sm
}

# Create necessary directories
mkdir -p uploads output templates logs

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A app.services.celery_app worker --loglevel=info --detach

# Start the FastAPI application
echo "Starting FastAPI application..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
