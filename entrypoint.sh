#!/bin/bash
set -e

# Get the PORT from environment variable or default to 8080
export PORT=${PORT:-8080}
# For Railway: nginx listens on PORT, API runs on internal port 8081
export API_PORT=8081

echo "=== Railway Startup Debug ==="
echo "Environment PORT (nginx): $PORT"
echo "Internal API_PORT: $API_PORT"
echo "Current working directory: $(pwd)"
echo "Files in /etc/nginx/sites-available/:"
ls -la /etc/nginx/sites-available/ || true
echo "=============================="

# Create logs directory with proper permissions
mkdir -p /app/logs
chown -R botuser:botuser /app/logs
chmod -R 755 /app/logs

# Substitute PORT in nginx config
echo "Configuring nginx for PORT: $PORT"
envsubst '${PORT}' < /etc/nginx/sites-available/default > /tmp/nginx.conf

# Substitute API_PORT placeholder
echo "Setting API proxy to localhost:$API_PORT"
sed "s/API_PORT_PLACEHOLDER/${API_PORT}/g" /tmp/nginx.conf > /etc/nginx/sites-available/default

echo "Final nginx config:"
cat /etc/nginx/sites-available/default

# Update supervisor config with correct API port
echo "Updating supervisor config for API_PORT: $API_PORT"
sed -i "s/PORT=8081/PORT=${API_PORT}/g" /etc/supervisor/conf.d/supervisord.conf

echo "Final supervisor config:"
cat /etc/supervisor/conf.d/supervisord.conf

# Test nginx configuration
echo "Testing nginx configuration..."
nginx -t

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
echo "=============================="

# Test API startup manually first
echo "Testing API startup..."
cd /app
echo "Testing Python API import..."
python test_api_startup.py || {
    echo "❌ API startup test failed!"
    exit 1
}

echo "✅ API startup test passed - proceeding with supervisor startup"

# Test running as botuser (same as supervisor will do)
echo "Testing API as botuser (same as supervisor)..."
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

echo "Starting services..."
# Start supervisor (which starts both nginx and the API)
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf