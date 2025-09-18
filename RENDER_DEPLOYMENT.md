# Render.com Deployment Guide for Amazon Job Monitor

## Quick Deployment Steps

### 1. Environment Variables
Set these in your Render service dashboard:

**Required:**
```
API_PORT=8000
USE_SELENIUM=true
POLL_INTERVAL=30
DATABASE_PATH=/app/data/jobs.db
LOG_LEVEL=INFO
AUTO_START_MONITORING=true
```

**Optional (for notifications):**
```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 2. Build Settings
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python api_bot.py`
- **Environment:** `Docker`

### 3. Service Configuration
- **Instance Type:** Free tier (512MB RAM minimum)
- **Region:** Choose closest to your location
- **Auto-Deploy:** Enable from main branch

### 4. Health Check
The service includes a health check endpoint at `/status`

### 5. Accessing Your Service
Once deployed, your service will be available at:
`https://your-service-name.onrender.com`

### 6. API Endpoints
- `GET /` - Service status
- `GET /jobs` - List detected jobs
- `GET /status` - Monitoring status
- `POST /start` - Start monitoring
- `POST /stop` - Stop monitoring
- `GET /logs` - View logs

### 7. Troubleshooting
If you see Chrome driver errors:
1. Check the logs in Render dashboard
2. Ensure all environment variables are set
3. The service will automatically fall back to requests-only mode if Chrome fails

### 8. Monitoring
- Check service logs in Render dashboard
- Use `/logs` endpoint to see application logs
- Monitor `/status` endpoint for service health