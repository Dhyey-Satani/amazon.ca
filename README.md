# Amazon Job Monitor API

🚀 **Live Production API for Amazon Job Monitoring**

A robust FastAPI-based job monitoring system that scrapes Amazon hiring pages and provides real-time job alerts.

## ✨ Features

- **Real-time Job Monitoring**: Continuously monitors Amazon hiring pages
- **REST API**: Full-featured API with job listing, status, and configuration endpoints
- **Selenium Support**: JavaScript rendering for accurate job detection
- **Fallback Mode**: Graceful degradation when Selenium fails
- **Cloud Ready**: Optimized for Render.com deployment

## 🚀 Quick Deployment

### Deploy to Render.com

1. **Connect your repository** to Render
2. **Set environment variables**:
   ```
   USE_SELENIUM=true
   API_PORT=8000
   AUTO_START_MONITORING=true
   POLL_INTERVAL=30
   ```
3. **Deploy** using the included Dockerfile

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
python api_bot.py
```

## 📡 API Endpoints

- `GET /` - API status
- `GET /jobs` - List detected jobs
- `GET /status` - Monitoring status
- `GET /logs` - Recent logs
- `POST /start` - Start monitoring
- `POST /stop` - Stop monitoring
- `DELETE /jobs` - Clear job history

## 🛠️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_SELENIUM` | `true` | Enable JavaScript rendering |
| `API_PORT` | `8000` | API server port |
| `POLL_INTERVAL` | `30` | Check interval (seconds) |
| `AUTO_START_MONITORING` | `true` | Auto-start on deployment |
| `AMAZON_URLS` | Amazon CA hiring page | Target URLs to monitor |

## 📋 Files

- `api_bot.py` - Main FastAPI application
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies
- `jobs.json` - Job storage (auto-generated)

## 🔧 Troubleshooting

For deployment issues, check the logs via the `/logs` endpoint.

---

**Ready for production deployment!** 🎉
