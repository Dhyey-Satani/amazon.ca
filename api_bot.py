#!/usr/bin/env python3
"""
Amazon Job Scraper Bot - Pay Rate Focus
Specifically targets jobs with "Pay rate" information from Amazon hiring page.
"""

import os
import json
import logging
import time
import tempfile
import threading
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import deque

from bs4 import BeautifulSoup

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure minimal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class JobPosting:
    """Job posting with pay rate information."""
    job_id: str
    title: str
    url: str
    location: str
    pay_rate: str
    description: str = ""
    detected_at: str = ""
    
    def __post_init__(self):
        if not self.detected_at:
            self.detected_at = datetime.now().isoformat()

class LiveJobScraper:
    """Live job scraper using ONLY Playwright for Amazon hiring page."""
class AmazonJobScraper:
    """Amazon job scraper focusing on Pay rate jobs using Playwright."""
    
    def __init__(self):
        self.logger = logging.getLogger('amazon-scraper')
        self.playwright = None
        self.browser = None
        self.context = None
        # Don't initialize Playwright immediately in async context
    
    def _ensure_browser(self):
        """Ensure browser is initialized when needed."""
        if self.browser is None:
            self.setup_playwright()
        return self.browser is not None
    
    def setup_playwright(self):
        """Setup Playwright browser with custom Chrome installation."""
        try:
            self.logger.info("Initializing Playwright browser...")
            
            # Import here to avoid async context issues
            from playwright.sync_api import sync_playwright
            
            self.playwright = sync_playwright().start()
            
            # Use the manually installed Chrome from Downloads
            chrome_path = r"C:\Users\HP\Downloads\chrome-win\chrome.exe"
            
            if os.path.exists(chrome_path):
                self.logger.info(f"Using manually installed Chrome: {chrome_path}")
                # Launch browser with explicit executable path
                self.browser = self.playwright.chromium.launch(
                    headless=True,
                    executable_path=chrome_path,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--window-size=1920,1080',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--allow-running-insecure-content'
                    ]
                )
            else:
                # Fallback to default Playwright browser
                self.logger.info("Chrome not found at expected path, using default Playwright browser")
                self.browser = self.playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--window-size=1920,1080',
                        '--disable-blink-features=AutomationControlled'
                    ]
                )
            
            # Create context with unique user data directory to avoid conflicts
            user_data_dir = tempfile.mkdtemp(prefix="chrome_session_")
            
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.logger.info("Playwright browser ready")
            
        except Exception as e:
            self.logger.error(f"Playwright setup failed: {e}")
            self.browser = None
            self.context = None
    
    def scrape_amazon_jobs(self, url: str = "https://hiring.amazon.ca/app#/jobsearch") -> tuple[List[JobPosting], List[str]]:
        """Scrape Amazon jobs using subprocess to avoid threading issues."""
        jobs = []
        page_messages = []
        
        try:
            self.logger.info(f"Starting subprocess scraper for: {url}")
            
            # Run the simple scraper in a subprocess
            result = subprocess.run(
                [sys.executable, "simple_scraper.py"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                # Parse the JSON output
                scrape_data = json.loads(result.stdout)
                
                if scrape_data.get("success"):
                    page_messages.extend(scrape_data.get("page_messages", []))
                    
                    # Convert jobs to JobPosting objects
                    for job_data in scrape_data.get("jobs", []):
                        job = JobPosting(
                            job_id=job_data["job_id"],
                            title=job_data["title"], 
                            url=job_data["url"],
                            location=job_data["location"],
                            pay_rate=job_data["pay_rate"],
                            description=job_data["description"]
                        )
                        jobs.append(job)
                        
                    self.logger.info(f"Subprocess scraper found {len(jobs)} Pay rate jobs")
                else:
                    page_messages.append("Subprocess scraper failed")
            else:
                error_msg = result.stderr.strip() or "Unknown subprocess error"
                page_messages.append(f"Subprocess error: {error_msg}")
                self.logger.error(f"Subprocess failed: {error_msg}")
                
        except subprocess.TimeoutExpired:
            page_messages.append("Scraping timeout after 60 seconds")
            self.logger.error("Subprocess timeout")
        except json.JSONDecodeError as e:
            page_messages.append(f"Failed to parse scraper output: {str(e)}")
            self.logger.error(f"JSON decode error: {e}")
        except Exception as e:
            page_messages.append(f"Scraping error: {str(e)}")
            self.logger.error(f"Subprocess scraping error: {e}")
        
        return jobs, page_messages
    
    def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            self.logger.warning(f"Cleanup warning: {e}")

class AmazonJobMonitor:
    """Amazon job monitor for Pay rate focused jobs."""
    
    def __init__(self):
        self.scraper = AmazonJobScraper()
        self.jobs: Dict[str, JobPosting] = {}
        self.logs = deque(maxlen=50)  # Reduced log size
        self.stats = {
            'total_checks': 0,
            'jobs_with_pay_rate': 0,
            'last_check_time': None
        }
        
        self.target_url = 'https://hiring.amazon.ca/app#/jobsearch'
        self.logger = logging.getLogger('monitor')
        
        # Initial log
        self.add_log('INFO', 'Amazon Pay Rate Job Monitor started')
        
        # Initialize browser in a separate thread to avoid blocking startup
        def init_browser():
            self.scraper._ensure_browser()
            browser_status = "Ready" if self.scraper.browser else "Failed"
            self.add_log('INFO', f'Browser initialization: {browser_status}')
        
        browser_thread = threading.Thread(target=init_browser)
        browser_thread.daemon = True
        browser_thread.start()
    
    def add_log(self, level: str, message: str):
        """Add simplified log entry."""
        log_entry = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        
        # Console log
        if level == 'ERROR':
            self.logger.error(message)
        else:
            self.logger.info(message)
    
    def check_for_jobs(self) -> dict:
        """Check for jobs with Pay rate information."""
        self.stats['total_checks'] += 1
        self.stats['last_check_time'] = datetime.now().isoformat()
        
        self.add_log('INFO', f'Starting job check #{self.stats["total_checks"]}')
        
        try:
            jobs, page_messages = self.scraper.scrape_amazon_jobs(self.target_url)
            
            # Log page messages
            for msg in page_messages:
                self.add_log('INFO', msg)
            
            new_jobs_count = 0
            for job in jobs:
                if job.job_id not in self.jobs:
                    self.jobs[job.job_id] = job
                    new_jobs_count += 1
                    self.add_log('SUCCESS', f'New Pay rate job: {job.title}')
            
            self.stats['jobs_with_pay_rate'] = len(self.jobs)
            
            if new_jobs_count > 0:
                self.add_log('SUCCESS', f'Found {new_jobs_count} new Pay rate jobs')
            else:
                self.add_log('INFO', 'No new Pay rate jobs found')
            
            return {
                'new_jobs': new_jobs_count,
                'total_jobs': len(self.jobs),
                'page_messages': page_messages
            }
            
        except Exception as e:
            self.add_log('ERROR', f'Job check failed: {str(e)}')
            return {'error': str(e)}
    
    def get_jobs(self, limit: int = 20) -> List[Dict]:
        """Get Pay rate jobs list."""
        jobs_list = list(self.jobs.values())
        jobs_list.sort(key=lambda x: x.detected_at, reverse=True)
        return [asdict(job) for job in jobs_list[:limit]]
    
    def get_status(self) -> Dict:
        """Get monitor status."""
        return {
            'is_running': True,
            'target_url': self.target_url,
            'browser_ready': bool(self.scraper.browser),
            'total_pay_rate_jobs': len(self.jobs),
            'stats': self.stats,
            'last_update': datetime.now().isoformat()
        }
    
    def get_logs(self, limit: int = 30) -> List[Dict]:
        """Get recent logs."""
        return list(self.logs)[-limit:]
    
    def clear_logs(self):
        """Clear all logs."""
        self.logs.clear()
        self.add_log('INFO', 'Logs cleared')
    
    def clear_jobs(self):
        """Clear all jobs."""
        count = len(self.jobs)
        self.jobs.clear()
        self.stats['jobs_with_pay_rate'] = 0
        self.add_log('INFO', f'Cleared {count} jobs')

# Initialize the job monitor
job_monitor = AmazonJobMonitor()

# Create FastAPI app
app = FastAPI(
    title="Amazon Pay Rate Job Monitor API",
    description="Scrapes Amazon jobs focusing on Pay rate information",
    version="3.0.0-payrate"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT", "PATCH"],
    allow_headers=["*"],
)

# Pydantic models
class StartMonitorRequest(BaseModel):
    check_immediately: Optional[bool] = True

# API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    browser_status = "✅ Ready" if job_monitor.scraper.browser else "❌ Not Ready"
    return {
        "message": "Amazon Pay Rate Job Monitor API",
        "version": "3.0.0-payrate",
        "target_url": "https://hiring.amazon.ca/app#/jobsearch",
        "focus": "Jobs with Pay rate information only",
        "browser_status": browser_status,
        "status": "running"
    }

@app.get("/jobs")
async def get_jobs(limit: int = 20):
    """Get Pay rate jobs (triggers fresh scraping)."""
    try:
        result = job_monitor.check_for_jobs()
        jobs = job_monitor.get_jobs(limit)
        return {
            "jobs": jobs,
            "total_pay_rate_jobs": len(job_monitor.jobs),
            "new_jobs_found": result.get('new_jobs', 0),
            "focus": "Pay rate jobs only",
            "page_messages": result.get('page_messages', [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get current monitoring status."""
    try:
        return job_monitor.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start")
async def start_monitoring(request: Optional[StartMonitorRequest] = None):
    """Trigger Pay rate job check."""
    try:
        result = job_monitor.check_for_jobs()
        return {
            "message": "Pay rate job check completed",
            "status": "success",
            "new_jobs_found": result.get('new_jobs', 0),
            "total_jobs": result.get('total_jobs', 0),
            "page_messages": result.get('page_messages', [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs")
async def get_logs(limit: int = 30):
    """Get recent log messages."""
    try:
        logs = job_monitor.get_logs(limit)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/logs")
async def clear_logs():
    """Clear all log messages."""
    try:
        job_monitor.clear_logs()
        return {"message": "Logs cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/jobs")
async def clear_jobs():
    """Clear all job history."""
    try:
        job_monitor.clear_jobs()
        return {"message": "Job history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    browser_ready = bool(job_monitor.scraper.browser)
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "browser_ready": browser_ready,
        "target_url": "https://hiring.amazon.ca/app#/jobsearch",
        "focus": "Pay rate jobs only"
    }

# API can be run with: uvicorn api_bot:app --host 0.0.0.0 --port 8000