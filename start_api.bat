@echo off
echo Starting Amazon Job Monitor API Server...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Python found!
echo Starting FastAPI server on http://localhost:8000
echo.
echo API Endpoints:
echo - http://localhost:8000/status
echo - http://localhost:8000/jobs  
echo - http://localhost:8000/logs
echo - http://localhost:8000/docs (Swagger UI)
echo.

REM Start the API server
python -m uvicorn api_bot:app --host localhost --port 8000 --log-level info

pause