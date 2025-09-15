#!/bin/bash

echo "🧪 Testing unified Docker build..."

# Check if required files exist
echo "📁 Checking required files..."
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found"
    exit 1
fi

if [ ! -d "job-monitor-frontend" ]; then
    echo "❌ job-monitor-frontend directory not found"
    exit 1
fi

if [ ! -f "job-monitor-frontend/package.json" ]; then
    echo "❌ job-monitor-frontend/package.json not found"
    exit 1
fi

if [ ! -f "api_bot.py" ]; then
    echo "❌ api_bot.py not found"
    exit 1
fi

echo "✅ All required files found"

echo "🔧 Building Docker image..."
docker build -t amazon-job-monitor-test . || {
    echo "❌ Docker build failed"
    exit 1
}

echo "✅ Docker build successful!"

echo "🚀 Testing container startup..."
docker run -d --name test-container -p 8080:8080 amazon-job-monitor-test || {
    echo "❌ Container startup failed"
    exit 1
}

echo "⏳ Waiting for services to start..."
sleep 30

echo "🔍 Testing frontend..."
curl -f http://localhost:8080/ > /dev/null 2>&1 || {
    echo "❌ Frontend not accessible"
    docker logs test-container
    docker rm -f test-container
    exit 1
}

echo "🔍 Testing API..."
curl -f http://localhost:8080/api/status > /dev/null 2>&1 || {
    echo "❌ API not accessible"
    docker logs test-container
    docker rm -f test-container
    exit 1
}

echo "✅ All tests passed!"
echo "🧹 Cleaning up..."
docker rm -f test-container
docker rmi amazon-job-monitor-test

echo "🎉 Unified container build is ready for Railway deployment!"