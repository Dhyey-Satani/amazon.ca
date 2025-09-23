# Amazon Pay Rate Job Monitor

🎯 **Production-ready job monitoring system** that scrapes Amazon's hiring page specifically for positions with "Pay rate" information.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM
- Internet connection

### One-Click Deployment

#### Linux/macOS:
```bash
./deploy.sh
```

#### Windows:
```cmd
deploy.bat
```

### Manual Deployment

```bash
# Build and start
docker-compose up -d

# Check status
curl http://localhost:8000/health
```

## 📋 Features

- **🎯 Targeted Scraping**: Only Amazon Canada hiring page
- **💰 Pay Rate Focus**: Filters jobs containing "Pay rate" information
- **⚡ Fast & Reliable**: Playwright-powered browser automation
- **🐳 Docker Ready**: Production-ready containerization
- **📊 REST API**: Complete API with health checks
- **📝 Clean Logging**: Structured logs for monitoring
- **🔧 Production Ready**: Security, scaling, and monitoring built-in

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-----------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/status` | GET | Monitor status |
| `/jobs` | GET | Get Pay rate jobs |
| `/start` | POST | Trigger job check |
| `/logs` | GET | Get recent logs |
| `/logs` | DELETE | Clear logs |
| `/jobs` | DELETE | Clear job history |

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
WORKERS=1

# Logging
LOG_LEVEL=INFO

# Browser
USE_PLAYWRIGHT=true

# Target
TARGET_URL=https://hiring.amazon.ca/app#/jobsearch
```

---

**🎯 Target**: `https://hiring.amazon.ca/app#/jobsearch`  
**🔍 Focus**: Jobs with "Pay rate" information only  
**🚀 Status**: Production Ready
