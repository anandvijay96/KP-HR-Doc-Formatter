#!/usr/bin/env python3
"""
Simple startup script for HR Resume Formatter
Installs dependencies and starts the application
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and handle errors"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 Starting HR Resume Formatter...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    print(f"✅ Python {sys.version}")
    
    # Create directories
    directories = ['uploads', 'output', 'templates', 'logs']
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"📁 Created directory: {dir_name}")
    
    # Install dependencies
    print("📦 Installing dependencies...")
    if not run_command("pip install fastapi uvicorn python-multipart python-docx docxtpl redis aiofiles"):
        print("❌ Failed to install basic dependencies")
        return False
    
    # Try to install optional dependencies
    print("🔧 Installing optional dependencies...")
    run_command("pip install spacy pytesseract opencv-python", check=False)
    run_command("python -m spacy download en_core_web_sm", check=False)
    
    # Start Redis if available
    print("🔍 Checking for Redis...")
    if run_command("redis-server --version", check=False):
        print("🚀 Starting Redis...")
        subprocess.Popen("redis-server", shell=True)
    else:
        print("⚠️  Redis not found. Some features may not work.")
    
    # Start the application
    print("🌐 Starting FastAPI application...")
    print("📍 Application will be available at: http://localhost:8000")
    print("📖 API documentation at: http://localhost:8000/docs")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
