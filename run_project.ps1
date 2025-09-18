# Amazon.ca Job Monitor - Complete Project Runner
# This script automatically installs dependencies and runs both backend and frontend

param(
    [switch]$SkipDependencies,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$Help
)

function Show-Help {
    Write-Host "Amazon.ca Job Monitor - Project Runner" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\run_project.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipDependencies   Skip dependency installation"
    Write-Host "  -BackendOnly       Run only the backend API server"
    Write-Host "  -FrontendOnly      Run only the frontend development server"
    Write-Host "  -Help              Show this help message"
    Write-Host ""
    Write-Host "Default behavior: Install dependencies and run both backend and frontend"
    Write-Host ""
    exit
}

function Write-Header {
    param($Message)
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Yellow
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
}

function Test-Command {
    param($CommandName)
    try {
        Get-Command $CommandName -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Install-PythonDependencies {
    Write-Header "Installing Python Dependencies"
    
    # Check if Python is available
    if (-not (Test-Command "python")) {
        Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
        Write-Host "Please install Python 3.11+ from https://python.org/" -ForegroundColor Red
        exit 1
    }
    
    $pythonVersion = python --version
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
    
    # Check if virtual environment exists
    if (-not (Test-Path "venv")) {
        Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
            exit 1
        }
    }
    
    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
    
    # Upgrade pip
    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    
    # Install requirements
    Write-Host "Installing Python packages from requirements.txt..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install Python dependencies" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Python dependencies installed successfully!" -ForegroundColor Green
}

function Install-NodeDependencies {
    Write-Header "Installing Node.js Dependencies"
    
    # Check if npm is available
    if (-not (Test-Command "npm")) {
        Write-Host "ERROR: npm is not installed or not in PATH" -ForegroundColor Red
        Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Red
        exit 1
    }
    
    $npmVersion = npm --version
    Write-Host "npm found: v$npmVersion" -ForegroundColor Green
    
    # Navigate to frontend directory
    Set-Location "job-monitor-frontend"
    
    # Install dependencies
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing Node.js packages..." -ForegroundColor Yellow
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Failed to install Node.js dependencies" -ForegroundColor Red
            Set-Location ".."
            exit 1
        }
    } else {
        Write-Host "Node modules already installed, checking for updates..." -ForegroundColor Yellow
        npm update
    }
    
    Set-Location ".."
    Write-Host "Node.js dependencies installed successfully!" -ForegroundColor Green
}

function Start-Backend {
    Write-Header "Starting Backend API Server"
    
    # Ensure we're in virtual environment
    if (-not $env:VIRTUAL_ENV) {
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & ".\venv\Scripts\Activate.ps1"
    }
    
    Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
    Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Magenta
    Write-Host ""
    
    # Start the API server
    python -m uvicorn api_bot:app --host 0.0.0.0 --port 8000 --reload
}

function Start-Frontend {
    Write-Header "Starting Frontend Development Server"
    
    Set-Location "job-monitor-frontend"
    
    Write-Host "Starting React development server..." -ForegroundColor Yellow
    Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "Make sure the backend is running at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Magenta
    Write-Host ""
    
    # Start the development server
    npm run dev
}

function Start-BothServices {
    Write-Header "Starting Both Backend and Frontend Services"
    
    Write-Host "This will start both services in separate windows." -ForegroundColor Yellow
    Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host ""
    
    # Start backend in new PowerShell window
    Write-Host "Starting backend in new window..." -ForegroundColor Yellow
    $backendScript = @"
Set-Location '$PWD'
& '.\venv\Scripts\Activate.ps1'
Write-Host 'Backend API Server Starting...' -ForegroundColor Green
Write-Host 'Available at: http://localhost:8000' -ForegroundColor Cyan
Write-Host 'Documentation: http://localhost:8000/docs' -ForegroundColor Cyan
Write-Host ''
python -m uvicorn api_bot:app --host 0.0.0.0 --port 8000 --reload
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript
    
    # Wait a moment for backend to start
    Start-Sleep -Seconds 3
    
    # Start frontend in new PowerShell window
    Write-Host "Starting frontend in new window..." -ForegroundColor Yellow
    $frontendScript = @"
Set-Location '$PWD\job-monitor-frontend'
Write-Host 'Frontend Development Server Starting...' -ForegroundColor Green
Write-Host 'Available at: http://localhost:3000' -ForegroundColor Cyan
Write-Host ''
npm run dev
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript
    
    Write-Host ""
    Write-Host "Both services are starting in separate windows!" -ForegroundColor Green
    Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press any key to exit this script (services will continue running)..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Main execution
if ($Help) {
    Show-Help
}

Write-Header "Amazon.ca Job Monitor - Project Setup & Runner"

# Install dependencies unless skipped
if (-not $SkipDependencies) {
    if (-not $FrontendOnly) {
        Install-PythonDependencies
    }
    if (-not $BackendOnly) {
        Install-NodeDependencies
    }
} else {
    Write-Host "Skipping dependency installation..." -ForegroundColor Yellow
}

# Run the appropriate service(s)
if ($BackendOnly) {
    Start-Backend
} elseif ($FrontendOnly) {
    Start-Frontend
} else {
    Start-BothServices
}