# Amazon Job Monitor - Local Development Setup

## 🚀 Quick Start

### Option 1: Automated Full Setup (Recommended)
```bash
# Run the full application launcher
start_full_app.bat
```
This will automatically:
- ✅ Check Python and Node.js installations
- ✅ Install all dependencies
- ✅ Start backend API (http://localhost:5000)
- ✅ Start frontend dashboard (http://localhost:3000)

### Option 2: Manual Setup

#### Backend (API)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the Selenium-only API
python api_live.py
```
API will be available at: http://localhost:5000

#### Frontend (Dashboard)
```bash
cd amazon-frontend

# Install Node.js dependencies (first time only)
npm install

# Start development server
npm run dev
```
Frontend will be available at: http://localhost:3000

## 📱 Application Access Points

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Status**: http://localhost:5000/status
- **API Jobs**: http://localhost:5000/jobs
- **API Health**: http://localhost:5000/health

## 🔧 Configuration

- **Target Site**: https://hiring.amazon.ca/app#/jobsearch (single site as requested)
- **Scraping Method**: Selenium WebDriver only (per user preference)
- **Frontend Port**: 3000
- **Backend Port**: 5000

## 🎯 Features

### Backend (api_live.py)
- ✅ Selenium-only scraping (no fallback to requests)
- ✅ Single target site: hiring.amazon.ca
- ✅ Real-time job detection
- ✅ FastAPI REST endpoints
- ✅ Enhanced error handling

### Frontend Dashboard
- ✅ Real-time job monitoring
- ✅ Dark/Light mode toggle
- ✅ Auto-refresh (every 2 seconds)
- ✅ Music notifications for new jobs
- ✅ Interactive controls
- ✅ Logs and status monitoring

## 🎵 Music Notifications

The dashboard plays notification music when new jobs are found:
- Uses `Scam 1992 Bgm Ringtone.mp3` (place in `public/` folder)
- Plays for 15 seconds
- Can be disabled in UI
- Volume set to 70%

## 🛠 Troubleshooting

### Common Issues

1. **API not accessible from frontend**
   - Ensure backend is running on port 5000
   - Check CORS settings in api_live.py

2. **Selenium issues**
   - Install Chrome/Chromium browser
   - Check Chrome driver compatibility
   - Verify system PATH settings

3. **Frontend build errors**
   - Delete `node_modules` and run `npm install`
   - Check Node.js version (14+ recommended)

4. **Music not playing**
   - Place `Scam 1992 Bgm Ringtone.mp3` in `amazon-frontend/public/`
   - Check browser audio permissions

## 📦 Dependencies

### Backend
- FastAPI
- Selenium WebDriver
- BeautifulSoup4
- Chrome/Chromium browser

### Frontend
- React 19.1.1
- Vite
- Tailwind CSS
- Axios
- Framer Motion

## 🔄 Development Workflow

1. Start backend: `python api_live.py`
2. Start frontend: `cd amazon-frontend && npm run dev`
3. Open http://localhost:3000
4. Backend logs appear in API terminal
5. Frontend has hot reload for development

## 📊 API Endpoints

- `GET /` - API information
- `GET /jobs` - Get jobs (triggers fresh scraping)
- `GET /status` - Get monitoring status
- `POST /start` - Start monitoring
- `GET /logs` - Get recent logs
- `GET /health` - Health check

## 🎨 Frontend Components

- `Dashboard.jsx` - Main dashboard container
- `StatusCard.jsx` - Status display cards
- `JobTable.jsx` - Jobs listing table
- `Controls.jsx` - Monitoring controls
- `LogsPanel.jsx` - Activity logs
- `Header.jsx` - Navigation header
- `musicPlayer.js` - Music notification utility

## 🚀 Production Deployment

For production deployment, the API URL needs to be updated in:
- `amazon-frontend/src/api.js` - Change `API_BASE_URL`