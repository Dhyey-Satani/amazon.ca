# Amazon.ca Scraper - Backend Only

This is the backend-only version of the Amazon.ca job scraper. The frontend has been separated into a different directory.

## Project Structure

```
amazon.ca/                  # Backend only
├── api_bot.py             # FastAPI server
├── bot.py                 # Scraper bot
├── main.py                # Vercel entry point
├── requirements.txt       # Python dependencies
├── Dockerfile             # Backend-only container
├── docker-compose.yml     # Backend deployment
├── entrypoint.sh          # Container startup script
└── ...

amazon.ca.frontend/        # Frontend (separate)
└── job-monitor-frontend/  # React frontend
    ├── src/
    ├── package.json
    └── ...
```

## Features

- **Amazon.ca Web Scraping**: Automated job listing scraper
- **REST API**: FastAPI-based API for accessing scraped data
- **SQLite Database**: Local database for storing job data
- **Docker Support**: Containerized deployment
- **Health Monitoring**: Built-in health checks

## Quick Start

### Docker Deployment (Recommended)

1. **Build and run the backend container:**
   ```bash
   docker-compose up --build
   ```

2. **Access the API:**
   - API Base URL: `http://localhost:8080`
   - Health Check: `http://localhost:8080/health`
   - API Documentation: `http://localhost:8080/docs`

### Local Development

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   copy .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the API server:**
   ```bash
   python api_bot.py
   ```

## API Endpoints

- `GET /health` - Health check
- `GET /status` - Bot status
- `GET /jobs` - List scraped jobs
- `POST /start` - Start scraping
- `POST /stop` - Stop scraping
- `GET /logs` - View logs

## Configuration

Set these environment variables in your `.env` file:

```env
USE_SELENIUM=true
POLL_INTERVAL=10
LOG_LEVEL=INFO
DATABASE_PATH=/app/data/jobs.db
PORT=8080
```

## Cloud Deployment

### Railway
```bash
# Connect your repository to Railway
# Set environment variables in Railway dashboard
# Deploy automatically from git
```

### Vercel (Serverless)
```bash
# Use the serverless version
npm install -g vercel
vercel --prod
```

## Frontend Integration

The frontend is located in `C:\Users\HP\Downloads\amazon.ca.frontend\job-monitor-frontend`

To run the frontend separately:
```bash
cd C:\Users\HP\Downloads\amazon.ca.frontend\job-monitor-frontend
npm install
npm run dev
```

Update the frontend's API base URL to point to your backend deployment.

## Troubleshooting

1. **Docker build fails**: Check Chrome/ChromeDriver installation in Dockerfile
2. **API not accessible**: Verify port mapping and firewall settings
3. **Scraping issues**: Check if Amazon has updated their site structure
4. **Database errors**: Ensure proper file permissions for SQLite database

## Development

- **Backend**: Python 3.11, FastAPI, Selenium
- **Database**: SQLite
- **Container**: Docker with Python base image
- **Web Scraping**: Selenium + ChromeDriver

## Security Notes

- Runs as non-root user in container
- Limited resource allocation
- Health checks enabled
- No sensitive data in logs