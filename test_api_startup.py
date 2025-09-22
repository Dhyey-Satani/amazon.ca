#!/usr/bin/env python3
"""
Simple API startup test - helps identify import/dependency issues
"""
import os
import sys

print("=== API Startup Test ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Test basic imports
try:
    print("Testing basic imports...")
    import requests
    print("✅ requests imported successfully")
    
    import fastapi
    print("✅ fastapi imported successfully")
    
    import uvicorn
    print("✅ uvicorn imported successfully")
    
    import selenium
    print("✅ selenium imported successfully")
    
    from bs4 import BeautifulSoup
    print("✅ beautifulsoup4 imported successfully")
    
    print("Testing API module import...")
    import api_bot
    print("✅ api_bot module imported successfully")
    
    print("Testing FastAPI app creation...")
    app = api_bot.app
    print("✅ FastAPI app created successfully")
    
    print("Testing job monitor initialization...")
    monitor = api_bot.job_monitor
    print("✅ Job monitor initialized successfully")
    
    # Test port binding without actually starting the server
    port = int(os.getenv('PORT', '8081'))
    print(f"✅ Would bind to port: {port}")
    
    print("=== All tests passed! ===")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)