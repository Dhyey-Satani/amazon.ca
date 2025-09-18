# Amazon.ca Job Monitor - Quick Start Guide

This guide will help you quickly set up and run the complete Amazon.ca job monitoring project with both backend API and frontend dashboard.

## 🚀 Quick Start (Recommended)

### Option 1: One-Click Setup (Easiest)

1. **Check Requirements First:**
   ```bash
   .\check_requirements.bat
   ```
   This will verify you have Python and Node.js installed and offer to start the project automatically.

2. **Or Run Complete Setup:**
   ```bash
   .\run_complete_project.bat
   ```
   This single script will:
   - Install all Python dependencies
   - Install all Node.js dependencies  
   - Start both backend and frontend services

### Option 2: PowerShell Script (More Options)

```powershell
# Run everything (recommended)
.\run_project.ps1

# Run with options
.\run_project.ps1 -BackendOnly     # Only start backend
.\run_project.ps1 -FrontendOnly    # Only start frontend
.\run_project.ps1 -SkipDependencies # Skip installation, just run
.\run_project.ps1 -Help            # Show all options
```

## 📋 Prerequisites

Before running the scripts, make sure you have:

- **Python 3.11+** - Download from [python.org](https://python.org/)
- **Node.js 18+** - Download from [nodejs.org](https://nodejs.org/)

## 🎯 What The Scripts Do

### 1. `check_requirements.bat`
- Verifies Python and Node.js are installed
- Shows version information
- Offers to start the project automatically

### 2. `run_complete_project.bat` 
- **Installs Python dependencies** (FastAPI, Selenium, etc.)
- **Installs Node.js dependencies** (React, Vite, Tailwind)
- **Starts backend API** on http://localhost:8000
- **Starts frontend app** on http://localhost:3000
- Opens both in separate terminal windows

### 3. `run_project.ps1` (PowerShell)
- Same functionality as batch file
- Additional options for backend-only or frontend-only
- Better error handling and progress display

## 🌐 Accessing the Application

After running the setup script:

- **Main Application:** http://localhost:3000
- **API Backend:** http://localhost:8000  
- **API Documentation:** http://localhost:8000/docs

## 📁 Project Structure

```
amazon.ca/
├── run_complete_project.bat    # Main setup script (Windows)
├── run_project.ps1            # PowerShell setup script  
├── check_requirements.bat     # Requirement checker
├── api_bot.py                # Backend API server
├── bot.py                    # Core scraping logic
├── requirements.txt          # Python dependencies
├── job-monitor-frontend/     # React frontend
│   ├── package.json         # Node.js dependencies
│   └── src/                 # Frontend source code
└── README.md                # This file
```

## 🔧 Manual Setup (If Scripts Don't Work)

### Backend Setup:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend
python -m uvicorn api_bot:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup:
```bash
# Navigate to frontend directory
cd job-monitor-frontend

# Install dependencies
npm install

# Start frontend
npm run dev
```

## 🐛 Troubleshooting

### Common Issues:

1. **"Python not found"**
   - Install Python from python.org
   - Make sure to check "Add Python to PATH" during installation

2. **"npm not found"** 
   - Install Node.js from nodejs.org
   - Restart your command prompt after installation

3. **Permission errors**
   - Run scripts as Administrator
   - Or try: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` (PowerShell)

4. **Port already in use**
   - Kill any existing processes on ports 8000 or 3000
   - Or change ports in the configuration

### Getting Help:

- Check the console output for specific error messages
- Both backend and frontend will show detailed logs
- API documentation available at http://localhost:8000/docs

## 🎮 Using the Application

1. **Start Monitoring:** Click "Start Monitoring" in the frontend
2. **View Jobs:** Check the jobs table for detected positions
3. **Check Logs:** Monitor the logs panel for scraping activity  
4. **API Access:** Use the REST API at http://localhost:8000 for integration

## 🔄 Updating Dependencies

To update all dependencies:
```bash
# Update Python packages
pip install --upgrade -r requirements.txt

# Update Node.js packages  
cd job-monitor-frontend
npm update
```

---

**Happy job hunting! 🎯**