#!/bin/bash
# Production deployment script for Amazon Pay Rate Job Monitor

set -e

echo "🚀 Deploying Amazon Pay Rate Job Monitor..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs data

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t amazon-pay-rate-monitor:latest .

# Stop existing container if running
echo "🛑 Stopping existing container..."
docker-compose down 2>/dev/null || true

# Start the application
echo "▶️ Starting application..."
docker-compose up -d

# Wait for health check
echo "🔍 Waiting for application to be healthy..."
timeout=60
counter=0
until curl -f http://localhost:8000/health > /dev/null 2>&1; do
    if [ $counter -eq $timeout ]; then
        echo "❌ Application failed to start within $timeout seconds"
        docker-compose logs
        exit 1
    fi
    counter=$((counter + 1))
    sleep 1
done

echo "✅ Application is healthy and running!"
echo "🌐 API available at: http://localhost:8000"
echo "📊 Health check: http://localhost:8000/health"
echo "📋 Status: http://localhost:8000/status"

# Show running containers
echo "📦 Running containers:"
docker-compose ps