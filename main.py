#!/usr/bin/env python3
"""
Vercel entry point for Amazon Job Monitor API
This file serves as the entry point for Vercel deployment.
"""

import os
from api_bot import app

# Set environment variables for serverless
os.environ['VERCEL'] = '1'
os.environ['USE_SELENIUM'] = 'false'

# Export the FastAPI app for Vercel
# Vercel will automatically detect this and use it as the handler
handler = app

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)