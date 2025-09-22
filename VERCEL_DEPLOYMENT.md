# Amazon Job Monitor - Vercel Deployment (FIXED)

## ✅ **Status: Issues Resolved**

The `FileNotFoundError: main.py` and serverless function crashes have been fixed!

## Quick Deployment Steps

### 1. Install Vercel CLI (if not already installed)
```bash
npm install -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

### 3. Deploy from this directory
```bash
# Make sure you're in the project root directory
cd path/to/amazon.ca

# Test locally first (optional)
python test_simple_api.py

# Deploy to Vercel
vercel --prod
```

## 🔧 **What Was Fixed**

1. **Created missing main.py**: Entry point that Vercel was looking for
2. **Added simplified API**: [api_simple.py](api_simple.py) - more reliable for serverless
3. **Fixed import issues**: Robust error handling and fallback imports
4. **Optimized dependencies**: Minimal requirements for faster cold starts
5. **Removed problematic features**: No Selenium, no file operations, no threading

## 📁 **Files for Vercel Deployment**

- **main.py**: Entry point with error handling
- **api_simple.py**: Simplified, serverless-friendly API
- **vercel.json**: Vercel configuration
- **requirements-vercel.txt**: Minimal dependencies
- **.vercelignore**: Exclude unnecessary files
- **test_simple_api.py**: Local testing script

## 🧪 **Testing Before Deployment**

```bash
# Test the simplified API locally
python test_simple_api.py

# Should show:
# ✅ Successfully imported api_simple
# ✅ All endpoints found
# ✅ All tests passed! Ready for Vercel deployment
```

### 4. Environment Variables (Optional)
Set these in your Vercel dashboard if needed:
- `AMAZON_URLS`: Comma-separated list of Amazon URLs to monitor
- `POLL_INTERVAL`: How often to check (not really applicable for serverless)
- `USE_SELENIUM`: Set to "false" (Selenium doesn't work on Vercel)

## What's Included for Vercel

- **main.py**: Entry point for Vercel
- **vercel.json**: Vercel configuration
- **requirements-vercel.txt**: Minimal dependencies for serverless
- **.vercelignore**: Files to exclude from deployment

## Important Notes

1. **No Background Tasks**: Vercel functions are stateless, so continuous monitoring isn't possible
2. **API Only**: This deploys just the API endpoints - you'll need to deploy the frontend separately
3. **No File Storage**: Jobs aren't persisted between function calls
4. **No Selenium**: Uses only requests + BeautifulSoup for web scraping

## API Endpoints Available

- `GET /` - API info
- `GET /jobs` - Get current jobs (will scrape on demand)
- `GET /status` - API status
- `POST /start` - Start monitoring (single check in serverless)
- `GET /logs` - Get logs

## Frontend Deployment

The frontend should be deployed separately. You can:
1. Deploy to Vercel as a separate project from the `job-monitor-frontend` folder
2. Use any other static hosting service (Netlify, GitHub Pages, etc.)

## Alternative: Use Railway for Full Features

For background monitoring with persistent storage, consider deploying to Railway instead, which supports longer-running processes.