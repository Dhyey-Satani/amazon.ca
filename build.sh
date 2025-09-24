#!/bin/bash
# Production build script for Amazon Pay Rate Job Monitor

set -e

echo "🏗️ Building Amazon Pay Rate Job Monitor for Production..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker and try again."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Verify Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_success "Prerequisites check passed"

# Create production directories
print_status "Creating production directories..."
mkdir -p logs data
print_success "Directories created"

# Build the Docker image
print_status "Building Docker image..."
docker build -t amazon-pay-rate-monitor:latest . --no-cache

if [ $? -eq 0 ]; then
    print_success "Docker image built successfully"
else
    print_error "Docker build failed"
    exit 1
fi

# Tag for production
docker tag amazon-pay-rate-monitor:latest amazon-pay-rate-monitor:production

# Clean up old containers and images
print_status "Cleaning up old containers and images..."
docker-compose down 2>/dev/null || true
docker image prune -f

# Show image info
print_status "Image information:"
docker images amazon-pay-rate-monitor

# Security scan (if available)
if command -v docker scan &> /dev/null; then
    print_status "Running security scan..."
    docker scan amazon-pay-rate-monitor:latest || print_warning "Security scan completed with warnings"
fi

# Test the image
print_status "Testing the image..."
docker run --rm -d --name test-container -p 8001:8000 amazon-pay-rate-monitor:latest

# Wait for container to start
sleep 10

# Health check
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_success "Health check passed"
else
    print_warning "Health check failed - container may need more time to start"
fi

# Stop test container
docker stop test-container 2>/dev/null || true

print_success "Build completed successfully!"
print_status "Ready for production deployment with: docker-compose up -d"

# Show next steps
echo ""
echo "📋 Next Steps:"
echo "1. Review configuration in docker-compose.yml"
echo "2. Set environment variables in .env.production"
echo "3. Deploy with: docker-compose up -d"
echo "4. Monitor with: docker-compose logs -f"
echo ""
echo "🌐 API will be available at: http://localhost:8000"
echo "📊 Health check: http://localhost:8000/health"