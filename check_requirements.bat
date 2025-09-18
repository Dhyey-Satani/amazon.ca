@echo off
echo ================================================================
echo Amazon.ca Job Monitor - System Requirements Check
echo ================================================================
echo.

set "all_good=1"

REM Check Python
echo [1/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is NOT installed or not in PATH
    echo    Please install Python 3.11+ from https://python.org/
    set "all_good=0"
) else (
    for /f "tokens=2" %%i in ('python --version') do (
        echo ✅ Python found: %%i
    )
)

REM Check pip
echo.
echo [2/4] Checking pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is NOT available
    set "all_good=0"
) else (
    for /f "tokens=2" %%i in ('pip --version') do (
        echo ✅ pip found: %%i
    )
)

REM Check Node.js
echo.
echo [3/4] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is NOT installed or not in PATH
    echo    Please install Node.js from https://nodejs.org/
    set "all_good=0"
) else (
    for /f "tokens=*" %%i in ('node --version') do (
        echo ✅ Node.js found: %%i
    )
)

REM Check npm
echo.
echo [4/4] Checking npm...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm is NOT available
    set "all_good=0"
) else (
    for /f "tokens=*" %%i in ('npm --version') do (
        echo ✅ npm found: v%%i
    )
)

echo.
echo ================================================================
if "%all_good%"=="1" (
    echo ✅ ALL REQUIREMENTS MET!
    echo You can now run: run_complete_project.bat
    echo.
    echo Would you like to start the project now? [Y/N]
    set /p "choice=Choice: "
    if /i "!choice!"=="Y" (
        echo.
        echo Starting the complete project...
        call run_complete_project.bat
    )
) else (
    echo ❌ MISSING REQUIREMENTS!
    echo Please install the missing components above and try again.
)
echo ================================================================

pause