# Production-ready Amazon Pay Rate Job Monitor
FROM python:3.11-slim

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    TZ=UTC

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    # Essential system packages
    wget curl unzip \
    # Playwright browser dependencies
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 \
    libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libgtk-3-0 libgbm1 libasound2 \
    # Additional dependencies for headless operation
    libxss1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create application directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/bash appuser \
    && mkdir -p /app/logs /app/data \
    && chown -R appuser:appuser /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (as root for system-wide installation)
RUN playwright install chromium \
    && playwright install-deps chromium

# Copy application files
COPY api_bot.py simple_scraper.py start_api.py ./

# Set proper permissions
RUN chown -R appuser:appuser /app \
    && chmod +x start_api.py

# Switch to non-root user
USER appuser

# Create logs directory with proper permissions
RUN mkdir -p /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production environment variables
ENV USE_PLAYWRIGHT=true \
    LOG_LEVEL=INFO \
    API_PORT=8000 \
    WORKERS=1

# Expose port
EXPOSE 8000

# Use start script for production
CMD ["python", "start_api.py"]