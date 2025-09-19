# Koyeb Deployment Guide for Amazon Job Monitor

## Why Koyeb?
- **Free tier without credit card** requirement
- **Docker-based deployment** support
- **Auto-scaling** and global edge network
- **Simple deployment process**

## Quick Deployment Steps

### 1. Prepare Repository
Ensure your repository has:
- ✅ `api_bot.py` - Main FastAPI application
- ✅ `Dockerfile` - Container configuration
- ✅ `requirements.txt` - Dependencies

### 2. Deploy to Koyeb

1. **Go to** [koyeb.com](https://www.koyeb.com)
2. **Sign up** (no credit card required)
3. **Create new app** → **Deploy from GitHub**
4. **Select repository**: `amazon.ca`
5. **Build method**: Dockerfile
6. **Port**: 8000

### 3. Environment Variables

Set in Koyeb dashboard:

```
USE_SELENIUM=true
API_PORT=8000
AUTO_START_MONITORING=true
POLL_INTERVAL=30
LOG_LEVEL=INFO
```

### 4. Deployment Configuration

- **Instance Type**: Free (1 vCPU, 256MB RAM)
- **Region**: Choose closest to your location
- **Auto-scaling**: Min 1, Max 1 (free tier)

### 5. Health Check

The app includes health checks at:
- `/` - API status
- `/status` - Monitoring status

### 6. Access Your API

Once deployed, your API will be available at:
`https://your-app-name.koyeb.app`

### API Endpoints:
- `GET /jobs` - List detected jobs
- `GET /status` - Monitoring status
- `GET /logs` - Recent logs
- `POST /start` - Start monitoring
- `POST /stop` - Stop monitoring

## Advantages over Render

1. **No credit card required** for free tier
2. **Faster cold starts** with edge network
3. **Better resource allocation** for small apps
4. **Simpler deployment process**

## Troubleshooting

If Selenium fails:
- The app automatically falls back to requests-only mode
- Check logs in Koyeb dashboard
- API remains functional with enhanced parsing

---

**Ready for free deployment!** 🚀