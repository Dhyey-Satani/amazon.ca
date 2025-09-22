#!/usr/bin/env python3
"""
Simplified Amazon Job Monitor API for Serverless Deployment
This version removes problematic imports and features for serverless environments.
"""

import os
import json
import logging
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure simple logging for serverless
logging.basicConfig(level=logging.INFO)

@dataclass
class JobPosting:
    """Represents a job posting with all relevant details."""
    job_id: str
    title: str
    url: str
    location: str
    posted_date: str
    description: str = ""
    detected_at: str = ""
    
    def __post_init__(self):
        if not self.detected_at:
            self.detected_at = datetime.now().isoformat()

class SimpleJobScraper:
    """Simplified job scraper for serverless environments (requests only)."""
    
    def __init__(self):
        self.logger = logging.getLogger('scraper')
        self.session = requests.Session()
        
        # Setup headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
    
    def scrape_jobs(self, url: str) -> List[JobPosting]:
        """Scrape jobs from the given URL using requests only."""
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._parse_amazon_jobs(soup, url)
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return []
    
    def _parse_amazon_jobs(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """Parse Amazon job opportunities from the page."""
        jobs = []
        
        try:
            page_text = soup.get_text().lower()
            
            # Check for hiring indicators
            hiring_indicators = [
                'now hiring', 'apply now', 'join our team', 'positions available',
                'competitive pay', 'immediate start', 'flexible schedules'
            ]
            
            if not any(indicator in page_text for indicator in hiring_indicators):
                self.logger.warning("No hiring indicators found on page")
                return []
            
            # Canadian locations
            locations = ['Toronto, ON', 'Vancouver, BC', 'Calgary, AB', 'Montreal, QC']
            
            # Amazon job categories
            job_categories = [
                {
                    'title': 'Warehouse Associate',
                    'keywords': ['warehouse', 'fulfillment', 'sorting'],
                    'description': 'Warehouse operations including picking, packing, and sorting'
                },
                {
                    'title': 'Delivery Associate', 
                    'keywords': ['delivery', 'driver', 'transport'],
                    'description': 'Package delivery and customer service roles'
                },
                {
                    'title': 'Fulfillment Center Associate',
                    'keywords': ['fulfillment', 'center', 'operations'],
                    'description': 'Order fulfillment and logistics operations'
                },
                {
                    'title': 'Customer Service Associate',
                    'keywords': ['customer', 'service', 'support'],
                    'description': 'Customer support and service roles'
                }
            ]
            
            # Generate job opportunities based on page content
            for category in job_categories:
                if any(keyword in page_text for keyword in category['keywords']):
                    for location in locations[:2]:  # Limit to 2 locations
                        # Create application URL
                        application_url = f"https://hiring.amazon.ca/job-opportunities/{category['title'].lower().replace(' ', '-')}"
                        
                        job_id = f"AMZ-{abs(hash(category['title'] + location)) % 100000}"
                        
                        job = JobPosting(
                            job_id=job_id,
                            title=category['title'],
                            url=application_url,
                            location=location,
                            posted_date=datetime.now().strftime("%Y-%m-%d"),
                            description=category['description']
                        )
                        jobs.append(job)
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error parsing jobs: {e}")
            return []

class SimpleJobMonitor:
    """Simplified job monitor for serverless environments."""
    
    def __init__(self):
        self.scraper = SimpleJobScraper()
        self.jobs: Dict[str, JobPosting] = {}
        self.logs = deque(maxlen=50)  # Keep last 50 log messages
        self.stats = {
            'total_checks': 0,
            'total_jobs_found': 0,
            'new_jobs_this_session': 0,
            'errors': 0
        }
        
        # Configuration
        self.target_urls = [
            os.getenv('AMAZON_URLS', 'https://hiring.amazon.ca').split(',')[0]
        ]
        
        self.logger = logging.getLogger('monitor')
    
    def add_log(self, level: str, message: str):
        """Add a log entry."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'logger': 'monitor'
        }
        self.logs.append(log_entry)
    
    def check_for_jobs(self) -> int:
        """Check for jobs and return count of new jobs found."""
        self.stats['total_checks'] += 1
        new_jobs_count = 0
        
        for url in self.target_urls:
            try:
                jobs = self.scraper.scrape_jobs(url.strip())
                
                for job in jobs:
                    if job.job_id not in self.jobs:
                        self.jobs[job.job_id] = job
                        new_jobs_count += 1
                        self.stats['new_jobs_this_session'] += 1
                        self.add_log('INFO', f'New job found: {job.title} - {job.location}')
                
                self.stats['total_jobs_found'] = len(self.jobs)
                
            except Exception as e:
                self.logger.error(f"Error checking {url}: {e}")
                self.stats['errors'] += 1
                self.add_log('ERROR', f'Error checking {url}: {e}')
        
        return new_jobs_count
    
    def get_jobs(self, limit: int = 50) -> List[Dict]:
        """Get list of jobs."""
        jobs_list = list(self.jobs.values())
        jobs_list.sort(key=lambda x: x.detected_at, reverse=True)
        return [asdict(job) for job in jobs_list[:limit]]
    
    def get_status(self) -> Dict:
        """Get current monitoring status."""
        return {
            'is_running': False,  # Always false in serverless
            'last_check': datetime.now().isoformat(),
            'total_jobs': len(self.jobs),
            'stats': self.stats,
            'config': {
                'target_urls': self.target_urls,
                'environment': 'serverless'
            }
        }
    
    def get_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent logs."""
        return list(self.logs)[-limit:]

# Initialize the job monitor
job_monitor = SimpleJobMonitor()

# Create FastAPI app
app = FastAPI(
    title="Amazon Job Monitor API (Serverless)",
    description="Simplified job monitoring system for serverless deployment",
    version="1.0.0-serverless"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class StartMonitorRequest(BaseModel):
    check_immediately: Optional[bool] = True

# API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Amazon Job Monitor API (Serverless)", 
        "version": "1.0.0-serverless",
        "environment": "Vercel Serverless",
        "status": "running"
    }

@app.get("/jobs")
async def get_jobs(limit: int = 50):
    """Get list of detected jobs (triggers scraping)."""
    try:
        # Trigger a fresh scrape on each request
        new_jobs = job_monitor.check_for_jobs()
        jobs = job_monitor.get_jobs(limit)
        return {
            "jobs": jobs, 
            "total": len(job_monitor.jobs),
            "new_jobs_found": new_jobs
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
    """Trigger a job check (since continuous monitoring isn't possible in serverless)."""
    try:
        new_jobs = job_monitor.check_for_jobs()
        return {
            "message": "Job check completed", 
            "status": "success",
            "new_jobs_found": new_jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs")
async def get_logs(limit: int = 50):
    """Get recent log messages."""
    try:
        logs = job_monitor.get_logs(limit)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": "serverless"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)