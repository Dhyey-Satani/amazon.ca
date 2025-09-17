# Backend-only build for Amazon.ca scraper
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
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

# Backend-only setup - no frontend files needed

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create app directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r botuser && useradd -r -g botuser -s /bin/bash -d /app botuser

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot.py .
COPY api_bot.py .
COPY test_bot.py .
COPY health_check.py .
COPY test_api_startup.py .
COPY diagnose_502.py .
COPY .env.example .

# Create necessary directories and set permissions
RUN mkdir -p logs data /var/log/supervisor && \
    chown -R botuser:botuser /app && \
    chmod +x /app/api_bot.py && \
    chmod +x /app/health_check.py && \
    chmod +x /app/diagnose_502.py && \
    # Ensure logs directory is writable by botuser
    chown -R botuser:botuser /app/logs && \
    chmod -R 755 /app/logs

# Switch to root user for supervisor (will run individual services as appropriate users)
USER root

# Health check for the API server
HEALTHCHECK --interval=5m --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Default environment variables
ENV USE_SELENIUM=true \
    POLL_INTERVAL=10 \
    LOG_LEVEL=INFO \
    DATABASE_PATH=/app/data/jobs.db \
    PORT=8081

# Expose port 8080 by default (Railway will override with PORT env var)
EXPOSE 8080

# Run the entrypoint script which configures and starts services
CMD ["/entrypoint.sh"]