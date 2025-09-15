@echo off
echo ================================
echo  Amazon Job Monitor - Vercel Deploy
echo ================================
echo.

echo Step 1: Testing the simplified API...
python test_simple_api.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: API test failed! Please fix the issues before deploying.
    pause
    exit /b 1
)

echo.
echo Step 2: Checking if Vercel CLI is installed...
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
echo - main.py (entry point with error handling)
echo - api_simple.py (simplified serverless API)
echo - vercel.json (configuration)
echo - requirements-vercel.txt (minimal dependencies)
echo - .vercelignore (exclusions)
echo.

echo Step 3: Starting Vercel deployment...
echo.

REM Deploy to Vercel
vercel --prod

echo.
echo ================================
echo Deployment complete!
echo.
echo Your API will be available at the URL shown above.
echo.
echo Test your deployed API:
echo - GET /health - Health check
echo - GET /jobs - Get jobs (triggers scraping)
echo - GET /status - API status
echo.
echo Don't forget to deploy the frontend separately!
echo ================================
pause