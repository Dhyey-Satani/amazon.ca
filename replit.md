# Amazon Job Monitor API

## Overview
This is a Python FastAPI-based application that monitors Amazon hiring pages and provides real-time job alerts through a REST API. The project has been successfully imported from GitHub and configured to run in the Replit environment.

## Project Structure
- **main.py** - Entry point for deployment, handles fallbacks between API versions
- **api_simple.py** - Simplified API version for serverless deployment (requests-only)
- **api_bot.py** - Full-featured API with Selenium support for JavaScript rendering
- **requirements.txt** - Python dependencies

## Key Features
- Real-time job monitoring from Amazon hiring pages
- REST API with multiple endpoints for job listing, status, and configuration
- Dual mode operation: simplified (requests-only) and full-featured (with Selenium)
- Cross-platform compatibility (Windows, Linux, Docker)
- Cloud deployment ready

## API Endpoints
- `GET /` - API status and information
- `GET /jobs` - List detected jobs (triggers fresh scraping)
- `GET /status` - Current monitoring status
- `GET /logs` - Recent log messages  
- `POST /start` - Start/trigger job monitoring
- `GET /health` - Health check endpoint

## Environment Configuration
- **USE_SELENIUM** - Enable/disable Selenium for JavaScript rendering
- **API_PORT** - Server port (defaults to 8000, but will run on 5000 in Replit)
- **POLL_INTERVAL** - Check interval in seconds
- **AUTO_START_MONITORING** - Auto-start monitoring on deployment
- **AMAZON_URLS** - Target URLs to monitor

## Recent Changes
- **2025-09-22**: Project imported from GitHub and configured for Replit environment
- **2025-09-22**: Python 3.11 and all required dependencies installed
- **2025-09-22**: Workflow configured to run FastAPI server on port 5000

## User Preferences
- Prefer the simplified API (api_simple.py) for better stability in cloud environments
- Use port 5000 for the frontend server in Replit
- Keep deployment configuration simple and robust

## Project Architecture
- **Backend**: FastAPI with uvicorn server
- **Scraping**: BeautifulSoup4 + requests (simplified) or Selenium (full-featured)
- **Database**: In-memory storage with optional JSON persistence
- **Deployment**: Optimized for cloud platforms (Vercel, Render, Railway)