@echo off
REM Production deployment script for Amazon Pay Rate Job Monitor (Windows)

echo 🚀 Deploying Amazon Pay Rate Job Monitor...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Create necessary directories
echo 📁 Creating directories...
if not exist logs mkdir logs
if not exist data mkdir data

REM Build the Docker image
echo 🔨 Building Docker image...
docker build -t amazon-pay-rate-monitor:latest .

REM Stop existing container if running
echo 🛑 Stopping existing container...
docker-compose down 2>nul

REM Start the application
echo ▶️ Starting application...
docker-compose up -d

REM Wait for health check
echo 🔍 Waiting for application to be healthy...
set timeout=60
set counter=0
:healthcheck
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    if %counter% equ %timeout% (
        echo ❌ Application failed to start within %timeout% seconds
        docker-compose logs
        exit /b 1
    )
    set /a counter+=1
    timeout /t 1 /nobreak >nul
    goto healthcheck
)

echo ✅ Application is healthy and running!
echo 🌐 API available at: http://localhost:8000
echo 📊 Health check: http://localhost:8000/health
echo 📋 Status: http://localhost:8000/status

REM Show running containers
echo 📦 Running containers:
docker-compose ps

pause