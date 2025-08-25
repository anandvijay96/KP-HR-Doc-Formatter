#!/bin/bash

# Test runner script for HR Resume Formatter

echo "Running HR Resume Formatter test suite..."

# Set environment variables for testing
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export TESTING=true

# Install test dependencies
echo "Installing test dependencies..."
pip install pytest pytest-asyncio pytest-cov

# Run tests with coverage
echo "Running tests with coverage..."
pytest tests/ \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-fail-under=80 \
    -v

# Generate coverage report
echo "Coverage report generated in htmlcov/"

# Run linting (if flake8 is available)
if command -v flake8 &> /dev/null; then
    echo "Running code linting..."
    flake8 app/ --max-line-length=100 --ignore=E203,W503
fi

echo "Test run completed!"
