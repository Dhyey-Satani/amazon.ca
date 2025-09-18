@echo off
setlocal enabledelayedexpansion

echo ================================================================
echo Amazon.ca Job Monitor - Complete Project Runner
echo ================================================================
echo.

REM Check if Python is available
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo Found: %%i

REM Check if npm is available
echo.
echo [2/6] Checking Node.js installation...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: npm is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('npm --version') do echo Found: npm v%%i

REM Create and activate virtual environment
echo.
echo [3/6] Setting up Python virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install Python dependencies
echo.
echo [4/6] Installing Python dependencies...
echo Upgrading pip...
python -m pip install --upgrade pip >nul
echo Installing packages from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
echo Python dependencies installed successfully!

REM Install Node.js dependencies
echo.
echo [5/6] Installing Node.js dependencies...
cd job-monitor-frontend
if not exist "node_modules" (
    echo Installing Node.js packages...
    npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install Node.js dependencies
        cd ..
        pause
        exit /b 1
    )
) else (
    echo Node modules already exist, checking for updates...
    npm update
)
cd ..
echo Node.js dependencies installed successfully!

REM Start both services
echo.
echo [6/6] Starting both services...
echo.
echo ================================================================
echo Starting Backend and Frontend Services
echo ================================================================
echo.
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:3000
echo API Documentation: http://localhost:8000/docs
echo.
echo Both services will start in separate windows.
echo Close this window or press Ctrl+C to stop monitoring the startup.
echo.

REM Start backend in new window
echo Starting backend API server...
start "Amazon.ca Job Monitor - Backend API" cmd /k "call venv\Scripts\activate.bat && echo Backend API Server Starting... && echo Available at: http://localhost:8000 && echo Documentation: http://localhost:8000/docs && echo. && python -m uvicorn api_bot:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window  
echo Starting frontend development server...
start "Amazon.ca Job Monitor - Frontend" cmd /k "cd job-monitor-frontend && echo Frontend Development Server Starting... && echo Available at: http://localhost:3000 && echo Backend should be at: http://localhost:8000 && echo. && npm run dev"

echo.
echo ================================================================
echo Services Started Successfully!
echo ================================================================
echo.
echo Backend API: http://localhost:8000
echo Frontend App: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Both services are running in separate windows.
echo You can now open your web browser and navigate to:
echo   - http://localhost:3000 (Main Application)
echo   - http://localhost:8000/docs (API Documentation)
echo.
echo Press any key to exit this launcher (services will continue running)...
pause >nul