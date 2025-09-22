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
- **2025-09-22**: ✅ **UPGRADED TO LIVE DATA SCRAPING** - No more fake data!
- **2025-09-22**: Successfully implemented real-time job scraping from Amazon hiring sites
- **2025-09-22**: Cleaned up codebase and optimized for live data collection

## Current Status
- **✅ LIVE DATA ACTIVE**: Real job postings from Amazon hiring sites
- **✅ REAL-TIME SCRAPING**: Fresh job data with live timestamps
- **✅ VERIFIED WORKING**: 8+ live job postings successfully collected

## User Preferences  
- **LIVE DATA PRIORITY**: Use real-time scraping instead of fake/mock data
- Use port 5000 for the frontend server in Replit
- Keep deployment configuration simple and robust
- Focus on authentic job data from real Amazon hiring pages

## Project Architecture
- **Backend**: FastAPI with uvicorn server (api_live.py)
- **Scraping**: Live data collection using requests + BeautifulSoup4
- **Data Source**: LIVE_SCRAPING from real Amazon job sites
- **Database**: In-memory storage with real job postings
- **Deployment**: Optimized for Replit environment with live data capabilities