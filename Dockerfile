# Multi-stage build: First stage for frontend build
FROM node:18-alpine as frontend-builder

# Set working directory for frontend
WORKDIR /frontend

# Copy frontend package files
COPY job-monitor-frontend/package*.json ./

# Install frontend dependencies
RUN npm ci --only=production

# Copy frontend source code
COPY job-monitor-frontend/ .

# Build frontend for production
RUN npm run build

# Second stage: Python backend with integrated frontend
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies including nginx
RUN apt-get update && apt-get install -y \
    # Chrome dependencies
    wget \
    gnupg \
    gpg \
    unzip \
    curl \
    xvfb \
    # Additional utilities
    cron \
    # Nginx for serving frontend
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Install ChromeDriver using Chrome for Testing API
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') && \
    echo "Chrome version: $CHROME_VERSION" && \
    CHROMEDRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | \
        python3 -c "import sys, json; data=json.load(sys.stdin); versions=[v for v in data['versions'] if v['version'].startswith('$CHROME_VERSION'.split('.')[0])]; print(versions[-1]['downloads']['chromedriver'][0]['url'] if versions and 'chromedriver' in versions[-1]['downloads'] else '')") && \
    if [ -z "$CHROMEDRIVER_URL" ]; then \
        # Fallback to latest stable if exact version not found
        CHROMEDRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" | \
            python3 -c "import sys, json; data=json.load(sys.stdin); print(data['channels']['Stable']['downloads']['chromedriver'][0]['url'])"); \
    fi && \
    echo "Downloading ChromeDriver from: $CHROMEDRIVER_URL" && \
    wget -O /tmp/chromedriver.zip "$CHROMEDRIVER_URL" && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    find /tmp -name chromedriver -type f -exec mv {} /usr/local/bin/chromedriver \; && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver* && \
    chromedriver --version

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /frontend/dist /var/www/html

# Create nginx configuration for serving frontend and proxying API
RUN cat > /etc/nginx/sites-available/default << 'EOF'
server {
    listen 8080;
    server_name localhost;
    root /var/www/html;
    index index.html;

    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;

    # Handle React Router
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8081/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Enable CORS
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        
        # Handle preflight requests
        if ($request_method = OPTIONS) {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 200;
        }
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
EOF

# Create supervisor configuration to run both nginx and python API
RUN cat > /etc/supervisor/conf.d/supervisord.conf << 'EOF'
[supervisord]
nodaemon=true
user=root

[program:nginx]
command=nginx -g "daemon off;"
autorestart=true
stdout_logfile=/var/log/nginx/access.log
stderr_logfile=/var/log/nginx/error.log

[program:api]
command=python /app/api_bot.py
directory=/app
autorestart=true
user=botuser
stdout_logfile=/app/logs/api.log
stderr_logfile=/app/logs/api.log
environment=PORT=8081
EOF

# Create app directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r botuser && useradd -r -g botuser -s /bin/bash botuser

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot.py .
COPY api_bot.py .
COPY test_bot.py .
COPY .env.example .

# Create necessary directories and set permissions
RUN mkdir -p logs data /var/log/nginx && \
    chown -R botuser:botuser /app && \
    chmod 755 /var/www/html

# Switch to root user for supervisor (will run individual services as appropriate users)
USER root

# Health check for the web server
HEALTHCHECK --interval=5m --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Default environment variables
ENV USE_SELENIUM=true \
    POLL_INTERVAL=10 \
    LOG_LEVEL=INFO \
    DATABASE_PATH=/app/data/jobs.db \
    PORT=8081

# Expose port 8080 for the combined frontend/backend service
EXPOSE 8080

# Run supervisor to manage both nginx and the API server
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]