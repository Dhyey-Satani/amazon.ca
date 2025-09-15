@echo off
echo 🧪 Testing unified Docker build...

echo 📁 Checking required files...
if not exist "Dockerfile" (
    echo ❌ Dockerfile not found
    exit /b 1
)

if not exist "job-monitor-frontend" (
    echo ❌ job-monitor-frontend directory not found
    exit /b 1
)

if not exist "job-monitor-frontend\package.json" (
    echo ❌ job-monitor-frontend\package.json not found
    exit /b 1
)

if not exist "api_bot.py" (
    echo ❌ api_bot.py not found
    exit /b 1
)

echo ✅ All required files found

echo 🔧 Building Docker image...
docker build -t amazon-job-monitor-test . 
if %errorlevel% neq 0 (
    echo ❌ Docker build failed
    exit /b 1
)

echo ✅ Docker build successful!

echo 🚀 Testing container startup...
docker run -d --name test-container -p 8080:8080 amazon-job-monitor-test
if %errorlevel% neq 0 (
    echo ❌ Container startup failed
    exit /b 1
)

echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak

echo 🔍 Testing frontend...
curl -f http://localhost:8080/ >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Frontend not accessible
    docker logs test-container
    docker rm -f test-container
    exit /b 1
)

echo 🔍 Testing API...
curl -f http://localhost:8080/api/status >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ API not accessible
    docker logs test-container
    docker rm -f test-container
    exit /b 1
)

echo ✅ All tests passed!
echo 🧹 Cleaning up...
docker rm -f test-container
docker rmi amazon-job-monitor-test

echo 🎉 Unified container build is ready for Railway deployment!