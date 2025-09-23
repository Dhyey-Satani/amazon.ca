#!/usr/bin/env python3
"""
Production startup script for Amazon Pay Rate Job Monitor API
"""

import os
import sys
import logging

def setup_logging():
    """Setup production logging."""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/app/logs/app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point for production."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        import uvicorn
        from api_bot import app
        
        # Production configuration
        port = int(os.getenv('API_PORT', 8000))
        host = os.getenv('API_HOST', '0.0.0.0')
        workers = int(os.getenv('WORKERS', 1))
        
        logger.info(f"🚀 Starting Amazon Pay Rate Job Monitor API")
        logger.info(f"📍 Host: {host}, Port: {port}")
        logger.info(f"🎯 Target: https://hiring.amazon.ca/app#/jobsearch")
        logger.info(f"🔍 Focus: Jobs with 'Pay rate' information only")
        logger.info(f"👥 Workers: {workers}")
        
        # Production uvicorn configuration
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=workers,
            log_level=os.getenv('LOG_LEVEL', 'info').lower(),
            access_log=True,
            loop="asyncio"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()