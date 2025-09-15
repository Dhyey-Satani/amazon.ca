@echo off
echo ================================
echo  Amazon Job Monitor - Vercel Deploy
echo ================================
echo.

echo Checking if Vercel CLI is installed...
where vercel >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Vercel CLI not found!
    echo Please install it first: npm install -g vercel
    pause
    exit /b 1
)

echo Vercel CLI found!
echo.

echo Current directory: %CD%
echo.

echo Files prepared for Vercel:
echo - main.py (entry point)
echo - vercel.json (configuration)
echo - requirements-vercel.txt (dependencies)
echo - .vercelignore (exclusions)
echo.

echo Starting Vercel deployment...
echo.

REM Deploy to Vercel
vercel --prod

echo.
echo ================================
echo Deployment complete!
echo.
echo Your API will be available at the URL shown above.
echo Don't forget to deploy the frontend separately from the job-monitor-frontend folder.
echo ================================
pause