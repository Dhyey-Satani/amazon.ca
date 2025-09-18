# amazon.ca
# Amazon.ca Job Scraper - Backend API

A backend service that monitors Amazon.ca for job postings and provides a REST API interface.

## Quick Start

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the API Server:**
   ```bash
   python api_bot.py
   ```

3. **Access the API:**
   - API Server: http://localhost:8080
   - API Documentation: http://localhost:8080/docs

## Docker Deployment

```bash
# Build and run
docker-compose up --build

# Access API at http://localhost:8080
```

## Frontend

The frontend has been moved to a separate repository for independent deployment.

## Features

- Real-time job monitoring from Amazon.ca
- REST API for job data access
- Selenium-based web scraping
- SQLite database storage
- Docker support
- Health checks and logging
