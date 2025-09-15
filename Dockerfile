# Use Python 3.11 slim image as base
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
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') && \
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%%.*}") && \
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

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

# Create necessary directories
RUN mkdir -p logs data && \
    chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Health check
HEALTHCHECK --interval=5m --timeout=30s --start-period=30s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('jobs.db') else 1)"

# Default environment variables
ENV USE_SELENIUM=true \
    POLL_INTERVAL=10 \
    LOG_LEVEL=INFO \
    DATABASE_PATH=/app/data/jobs.db

# Expose port for API
EXPOSE 8080

# Run the API server (Railway will handle the persistent data via volumes)
CMD ["python", "api_bot.py"]