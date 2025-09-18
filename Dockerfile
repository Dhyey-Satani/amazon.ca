# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    HOME=/app \
    CHROME_NO_SANDBOX=1 \
    DISPLAY=:99

# Install system dependencies including Chrome
RUN apt-get update && apt-get install -y \
    # Chrome dependencies
    wget \
    gnupg \
    gpg \
    unzip \
    curl \
    xvfb \
    # Chrome browser
    google-chrome-stable \
    # Additional utilities
    cron \
    && rm -rf /var/lib/apt/lists/*

# Add Google Chrome repository and install
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

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

# Switch to non-root user before copying app files
USER botuser

# Copy application code with proper ownership
COPY --chown=botuser:botuser bot.py .
COPY --chown=botuser:botuser api_bot.py .
COPY --chown=botuser:botuser test_bot.py .
COPY --chown=botuser:botuser .env.example .

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
    CHROME_BIN=/usr/bin/google-chrome

# Expose port for API
EXPOSE 8000

# Start virtual display for headless Chrome
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & python api_bot.py"]