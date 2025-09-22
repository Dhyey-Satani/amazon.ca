#!/usr/bin/env python3
"""
Replit Configuration for Amazon Job Monitor
Optimized for Replit's free hosting environment
"""

import os
import sys

# Replit-specific configuration
def setup_replit_environment():
    """Configure environment for Replit deployment."""
    
    # Set Replit-specific environment variables
    os.environ.setdefault('USE_SELENIUM', 'true')  # Replit supports Selenium
    os.environ.setdefault('API_PORT', '8000')
    os.environ.setdefault('AUTO_START_MONITORING', 'true')
    os.environ.setdefault('POLL_INTERVAL', '60')  # Longer interval for free tier
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    # Replit detection
    if 'REPL_ID' in os.environ:
        print("🎯 Detected Replit environment")
        os.environ['REPLIT_MODE'] = 'true'
        
        # Configure for Replit's network setup
        os.environ['HOST'] = '0.0.0.0'
        os.environ['PORT'] = str(os.environ.get('PORT', 8000))
        
        # Optimize for Replit's resources
        os.environ['WDM_CACHE_DIR'] = '/home/runner/.wdm'
        os.environ['CHROME_USER_DATA_DIR'] = '/tmp/chrome_user_data'
        
        return True
    return False

def install_dependencies():
    """Install required dependencies for Replit."""
    
    dependencies = [
        'fastapi',
        'uvicorn[standard]', 
        'requests',
        'beautifulsoup4',
        'selenium',
        'webdriver-manager',
        'python-dotenv'
    ]
    
    print("📦 Installing dependencies...")
    for dep in dependencies:
        try:
            __import__(dep.split('[')[0].replace('-', '_'))
            print(f"✅ {dep} already installed")
        except ImportError:
            print(f"⬇️  Installing {dep}...")
            os.system(f"pip install {dep}")

def setup_chrome_for_replit():
    """Setup Chrome/Selenium for Replit environment."""
    
    if not os.path.exists('/home/runner/.wdm'):
        os.makedirs('/home/runner/.wdm', exist_ok=True)
    
    if not os.path.exists('/tmp/chrome_user_data'):
        os.makedirs('/tmp/chrome_user_data', exist_ok=True)
    
    print("🌐 Chrome environment configured for Replit")

def main():
    """Main setup function for Replit."""
    
    print("🚀 Setting up Amazon Job Monitor for Replit...")
    print("=" * 50)
    
    # Setup environment
    is_replit = setup_replit_environment()
    
    if is_replit:
        print("✅ Replit environment detected and configured")
        
        # Install dependencies
        install_dependencies()
        
        # Setup Chrome
        setup_chrome_for_replit()
        
        print("\n" + "=" * 50)
        print("🎉 Setup complete! Starting your bot...")
        print(f"🌐 Your API will be available at: https://{os.environ.get('REPL_SLUG', 'your-repl')}.{os.environ.get('REPL_OWNER', 'username')}.repl.co")
        print("=" * 50)
        
        # Import and run the main application
        try:
            from api_bot import app
            import uvicorn
            
            host = os.environ.get('HOST', '0.0.0.0')
            port = int(os.environ.get('PORT', 8000))
            
            print(f"🚀 Starting server on {host}:{port}")
            uvicorn.run(app, host=host, port=port)
            
        except ImportError as e:
            print(f"❌ Error importing api_bot: {e}")
            print("Make sure api_bot.py is in the same directory")
            sys.exit(1)
            
    else:
        print("⚠️  Not running on Replit. Use this script only on Replit.")
        print("For local development, run: python api_bot.py")

if __name__ == "__main__":
    main()