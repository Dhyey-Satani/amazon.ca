@echo off
title Amazon Job Monitor - Full Application Startup
color 0A

echo ===============================================
echo       Amazon Job Monitor - Full Setup       
echo ===============================================
echo.
echo This script will start both:
echo   1. Backend API (Selenium-only scraping)
echo   2. React Frontend Dashboard
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org/
    pause
    exit /b 1
)
echo ✅ Python found!

REM Check Node.js installation
cd amazon-frontend
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: npm is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo ✅ Node.js/npm found!
cd ..

echo.
echo 📦 Installing/checking dependencies...

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Warning: Some Python dependencies may have failed to install
)

REM Install Node.js dependencies
echo Installing Node.js dependencies...
cd amazon-frontend
if not exist "node_modules" (
    npm install >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ ERROR: Failed to install Node.js dependencies
        pause
        exit /b 1
    )
)
cd ..

echo ✅ Dependencies ready!
echo.

echo 🚀 Starting applications...
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul

REM Start backend API in a new window
echo 🔧 Starting Backend API (Selenium-only)...
start "Amazon Job Monitor API" cmd /k "python api_live.py"

REM Wait a moment for API to start
timeout /t 5 /nobreak >nul

REM Start frontend in a new window
echo 🎨 Starting Frontend Dashboard...
cd amazon-frontend
start "Amazon Job Monitor Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ✅ Both applications are starting!
echo.
echo 📱 Access points:
echo    • Frontend Dashboard: http://localhost:3000
echo    • Backend API:        http://localhost:5000
echo    • API Status:         http://localhost:5000/status
echo    • API Jobs:           http://localhost:5000/jobs
echo.
echo 🎯 Target Site: https://hiring.amazon.ca/app#/jobsearch
echo 🔍 Scraping Method: Selenium WebDriver (as per user preference)
echo.
echo Press any key to close this launcher window...
pause >nul