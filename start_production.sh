#!/bin/bash
# Render.com Deployment Script for Amazon Job Monitor

echo "Starting Amazon Job Monitor API Server..."

# Set environment defaults for production
export USE_SELENIUM=${USE_SELENIUM:-true}
export POLL_INTERVAL=${POLL_INTERVAL:-30}
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export API_PORT=${API_PORT:-8000}
export DATABASE_PATH=${DATABASE_PATH:-/app/data/jobs.db}
export AUTO_START_MONITORING=${AUTO_START_MONITORING:-true}

# Create required directories
mkdir -p /app/data /app/logs /app/.cache

# Ensure proper permissions
chmod 755 /app/data /app/logs /app/.cache

# Start Xvfb for headless Chrome (if using Selenium)
if [ "$USE_SELENIUM" = "true" ]; then
    echo "Starting virtual display for headless Chrome..."
    Xvfb :99 -screen 0 1920x1080x24 &
    export DISPLAY=:99
fi

# Health check function
health_check() {
    echo "Performing health check..."
    if python -c "import requests; r=requests.get('http://localhost:$API_PORT/status', timeout=10); exit(0 if r.status_code==200 else 1)" 2>/dev/null; then
        echo "Health check passed"
        return 0
    else
        echo "Health check failed"
        return 1
    fi
}

# Start the API server
echo "Starting API server on port $API_PORT..."
python api_bot.py &
API_PID=$!

# Wait for server to start
sleep 10

# Perform initial health check
if health_check; then
    echo "API server started successfully (PID: $API_PID)"
else
    echo "Warning: API server may not be responding correctly"
fi

# Keep the script running
wait $API_PID