@echo off
echo Starting React Frontend Development Server...
echo.

REM Check if npm is available
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: npm is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo npm found!
echo.

REM Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Starting development server...
echo Frontend will be available at: http://localhost:3000
echo API should be running at: http://localhost:8000
echo.

REM Start the development server
npm run dev

pause