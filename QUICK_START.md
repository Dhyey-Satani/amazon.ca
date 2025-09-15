# Amazon Job Monitor - Quick Start Guide

## 🚀 Full Stack Setup (Frontend + Backend)

This guide will help you get both the frontend and backend running together using Docker.

### Prerequisites

- Docker and Docker Compose installed
- Git (for cloning)

### 🏗️ Setup Instructions

#### 1. Clone and Setup Environment

```bash
git clone <your-repo-url>
cd amazon.ca

# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
nano .env  # or use your preferred editor
```

#### 2. Build and Run with Docker Compose

```bash
# Build and start both frontend and backend
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

#### 3. Access the Application

- **Full Stack Application**: http://localhost:3000 (Local development)
- **Railway Deployment**: Your Railway URL will serve both frontend and backend
- **API Endpoints**: Available at `/api/*` (proxied through the frontend)

### 🔧 Development Commands

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f amazon-job-bot
docker-compose logs -f job-monitor-frontend

# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Rebuild and restart
docker-compose up --build

# Remove everything (including volumes)
docker-compose down -v
```

### 📁 Architecture

```
amazon.ca/
├── job-monitor-frontend/    # React frontend with Vite
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── bot.py                   # Main scraping bot
├── api_bot.py              # FastAPI backend
├── Dockerfile              # Backend container
├── docker-compose.yml      # Multi-service setup
└── requirements.txt        # Python dependencies
```

### 🐛 Troubleshooting

#### ChromeDriver Issues
The new setup uses Chrome for Testing API which is more reliable:
- Automatically matches Chrome version with ChromeDriver
- Fallback to latest stable if exact version not found

#### Port Conflicts
If port 3000 is already in use:
```yaml
# In docker-compose.yml, change:
ports:
  - "3001:80"  # Use port 3001 instead
```

#### Frontend API Connection
The frontend automatically detects the environment:
- **Development**: Connects to `http://localhost:8080`
- **Production**: Uses `/api` (proxied through nginx)

#### Container Health
Check container health:
```bash
docker-compose ps
docker health-check amazon-job-bot
```

### 🌐 Railway Deployment

The new unified Dockerfile automatically serves both frontend and backend:

**What happens on Railway:**
1. **Single Container**: One container serves both frontend (React) and backend (FastAPI)
2. **Nginx Proxy**: Nginx serves the React frontend and proxies `/api/*` calls to the Python backend
3. **Port 8080**: Railway exposes port 8080 which serves the complete application
4. **Frontend**: React app served at the root URL (`/`)
5. **Backend API**: Python FastAPI accessible via `/api/*` endpoints
6. **Data Persistence**: SQLite database stored in persistent volumes

**Railway Configuration:**
- Main service runs on port 8080
- Frontend served by nginx
- Backend runs internally on port 8081
- All API calls automatically proxied from `/api/*` to backend

**After successful deployment, your Railway URL will show:**
- Root path (`/`): Full React dashboard interface
- API paths (`/api/*`): JSON API responses

No more separate deployments needed - everything runs in one unified container!

### 📊 Features

- **Real-time Job Monitoring**: Track Amazon job listings
- **Web Dashboard**: Modern React UI with real-time updates
- **API Backend**: RESTful API with FastAPI
- **Data Persistence**: SQLite database with volume mounting
- **Health Monitoring**: Container health checks
- **Logging**: Structured logging with rotation
- **Security**: Non-root user execution, security headers