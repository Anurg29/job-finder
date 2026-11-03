@echo off
REM Backend Setup Script for Windows
REM This script sets up and runs the Job Search backend

echo ============================================================
echo    Job Search Backend - Setup ^& Deploy Script
echo ============================================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python: %PYTHON_VERSION%

echo.
echo Installing dependencies...
pip install -e .
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Setup .env file
if not exist ".env" (
    echo Setting up .env file...
    copy .env.example .env
    echo .env file created (you can edit it to add GROQ_API_KEY)
) else (
    echo .env file already exists
)
echo.

REM Start server
echo Starting backend server...
echo Server will run on: http://localhost:8002
echo Web UI: http://localhost:8002
echo Press CTRL+C to stop
echo.

uvicorn job_search.api:app --reload --port 8002

pause
