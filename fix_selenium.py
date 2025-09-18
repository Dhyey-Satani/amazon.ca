#!/usr/bin/env python3
"""
Quick fix script to disable Selenium completely and avoid permission issues
Run this to patch the API for immediate deployment fix
"""

import os
import sys

# Set environment variable to disable Selenium
os.environ['USE_SELENIUM'] = 'false'

# Import and patch the JobScraper class
if __name__ == "__main__":
    # Set the environment variable for the current process
    print("Setting USE_SELENIUM=false to avoid permission issues...")
    
    # Modify api_bot.py to force disable Selenium
    try:
        with open('api_bot.py', 'r') as f:
            content = f.read()
        
        # Replace the default value
        content = content.replace(
            "os.getenv('USE_SELENIUM', 'false').lower() == 'true'", 
            "False  # Force disabled for cloud deployment"
        )
        
        with open('api_bot.py', 'w') as f:
            f.write(content)
        
        print("✅ Successfully patched api_bot.py to disable Selenium")
        print("Your deployment should now work without permission errors!")
        
    except Exception as e:
        print(f"❌ Error patching file: {e}")
        sys.exit(1)