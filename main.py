#!/usr/bin/env python3
"""
Vercel entry point for Amazon Job Monitor API
This file serves as the entry point for Vercel deployment.
"""

import os
import sys
import traceback
from pathlib import Path

# Set environment variables for serverless BEFORE importing anything
os.environ['VERCEL'] = '1'
os.environ['USE_SELENIUM'] = 'false'
os.environ['PYTHONPATH'] = str(Path(__file__).parent)

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Try importing the simplified API first (more reliable for serverless)
    from api_simple import app
    print("Successfully imported simplified API")
except ImportError:
    try:
        # Fallback to full API
        from api_bot import app
        print("Successfully imported full API")
    except ImportError as e:
        # Create a simple error app if both imports fail
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        error_app = FastAPI(title="Error Handler")
        
        @error_app.get("/")
        async def error_root():
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Failed to import application",
                    "details": str(e),
                    "traceback": traceback.format_exc()
                }
            )
        
        app = error_app
        print(f"ERROR: Failed to import both APIs: {e}")

# Export for Vercel
handler = app

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)