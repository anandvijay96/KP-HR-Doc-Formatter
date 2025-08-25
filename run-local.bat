@echo off
echo Starting HR Resume Formatter locally...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Download spaCy model
echo Downloading spaCy model...
python -m spacy download en_core_web_sm

REM Create directories
echo Creating directories...
if not exist "uploads" mkdir uploads
if not exist "output" mkdir output
if not exist "templates" mkdir templates
if not exist "logs" mkdir logs

REM Start Redis (if available)
echo Checking for Redis...
redis-server --version >nul 2>&1
if not errorlevel 1 (
    echo Starting Redis server...
    start /B redis-server
) else (
    echo Redis not found. Install Redis or use Docker for Redis only.
)

REM Start the application
echo Starting FastAPI application...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
