# Amazon Job Monitor - Vercel Deployment

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

# Deploy to Vercel
vercel --prod
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