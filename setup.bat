@echo off
echo Amazon Job Monitor Bot - Local Setup
echo =====================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python is installed!
python --version

REM Install requirements
echo.
echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install requirements
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your Telegram bot credentials
echo 2. Run: python bot.py
echo.
pause