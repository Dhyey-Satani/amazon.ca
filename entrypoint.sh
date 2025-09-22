#!/bin/bash
set -e

# Backend-only entrypoint for Amazon.ca scraper
# Get the PORT from environment variable or default to 8080
export PORT=${PORT:-8080}

echo "=== Backend-Only Startup ==="
echo "API will bind to PORT: $PORT"
echo "Current working directory: $(pwd)"
echo "==========================="

# Create logs directory with proper permissions
mkdir -p /app/logs
chown -R botuser:botuser /app/logs
chmod -R 755 /app/logs

# Add debugging: Check Python and dependencies
echo "=== Python Environment Check ==="
echo "Python version:"
python --version
echo "Python executable:"
which python
echo "Pip packages:"
pip list | grep -E "(fastapi|uvicorn|requests)"
echo "API script exists:"
ls -la /app/api_bot.py
echo "API script permissions:"
stat /app/api_bot.py
echo "App directory permissions:"
ls -la /app/
echo "============================="

# Test API startup manually first
echo "Testing API startup..."
cd /app
echo "Testing Python API import..."
python test_api_startup.py || {
    echo "❌ API startup test failed!"
    exit 1
}

echo "✅ API startup test passed - proceeding with direct API startup"

# Test running as botuser
echo "Testing API as botuser..."
# Ensure botuser has full access to app directory and logs
chown -R botuser:botuser /app
chmod -R 755 /app
su - botuser -c "cd /app && python test_api_startup.py" || {
    echo "❌ API test failed when running as botuser!"
    echo "Checking permissions..."
    ls -la /app/
    echo "Checking logs directory..."
    ls -la /app/logs/ || echo "logs directory not found"
    echo "Checking botuser environment..."
    su - botuser -c "whoami && pwd && python --version"
    exit 1
}

echo "Starting API server directly..."
echo "API will bind to: 0.0.0.0:$PORT"

# Switch to botuser and start the API server
exec su - botuser -c "cd /app && PORT=$PORT python api_bot.py"