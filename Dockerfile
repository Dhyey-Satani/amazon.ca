# Backend-only build for Amazon.ca scraper
FROM python:3.11-slim

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    HOME=/app \
    CHROME_NO_SANDBOX=1 \
    DISPLAY=:99

# Install system dependencies first
RUN apt-get update && apt-get install -y \
    # Basic dependencies
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

# Add Google Chrome repository and install Chrome with error handling
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    (apt-get install -y google-chrome-stable || \
     # Fallback: Install chromium if google-chrome fails
     apt-get install -y chromium-browser) && \
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

# Create app directory first
WORKDIR /app

# Create non-root user with proper permissions
RUN groupadd -r botuser && useradd -r -g botuser -s /bin/bash botuser && \
    # Create necessary directories with proper permissions
    mkdir -p /app/logs /app/data /app/.cache /app/.local /app/chromedriver && \
    chown -R botuser:botuser /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api_bot.py .
COPY .env.example .

# Create necessary directories and set permissions
RUN mkdir -p logs data /var/log/supervisor && \
    chown -R botuser:botuser /app && \
    chmod +x /app/api_live.py && \
    chmod +x /app/health_check.py && \
    chmod +x /app/diagnose_502.py && \
    # Ensure logs directory is writable by botuser
    chown -R botuser:botuser /app/logs && \
    chmod -R 755 /app/logs

# Switch to non-root user
USER botuser

# Health check
HEALTHCHECK --interval=5m --timeout=30s --start-period=30s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('jobs.db') else 1)"

# Default environment variables for production
ENV USE_SELENIUM=true \
    POLL_INTERVAL=30 \
    LOG_LEVEL=INFO \
    DATABASE_PATH=/app/data/jobs.db \
    API_PORT=8000 \
    HOME=/app \
    WEBDRIVER_CHROME_DRIVER=/usr/bin/chromedriver \
    CHROME_BIN=/usr/bin/google-chrome \
    CHROME_USER_DATA_DIR=/app/.chrome_user_data

# Expose port for API
EXPOSE 8000

# Start the API bot
CMD ["python", "api_bot.py"]