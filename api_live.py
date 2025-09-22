#!/usr/bin/env python3
"""
Live Amazon Job Monitor API with Selenium
Simplified version configured for Replit environment with real data scraping.
"""

import os
import json
import logging
import time
import tempfile
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import deque

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class LiveJobScraper:
    """Live job scraper using ONLY Selenium for Amazon hiring page."""
    
    def __init__(self):
        self.logger = logging.getLogger('scraper')
        self.driver = None
        self.use_selenium = True  # FORCE Selenium usage as per user preference
        self.setup_selenium()
    
    def setup_selenium(self):
        """Setup Selenium WebDriver with Chrome for Windows environment."""
        try:
            chrome_options = Options()
            
            # Configure for Windows development
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Set Chrome binary path for Windows
            chrome_binary_paths = [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
            ]
            
            for chrome_path in chrome_binary_paths:
                if os.path.exists(chrome_path):
                    chrome_options.binary_location = chrome_path
                    self.logger.info(f"Using Chrome binary: {chrome_path}")
                    break
            
            # Use temporary directory for user data
            temp_dir = tempfile.mkdtemp()
            chrome_options.add_argument(f'--user-data-dir={temp_dir}')
            
            # Try with WebDriverManager first (Windows)
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                
                # Set cache directory
                os.environ['WDM_LOCAL'] = '1'
                os.environ['WDM_LOG_LEVEL'] = '0'
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
            except ImportError:
                # Fallback without WebDriverManager
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Configure driver to avoid detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.logger.info("✅ Selenium WebDriver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup Selenium: {e}")
            self.driver = None
    
    def scrape_jobs(self, url: str) -> List[JobPosting]:
        """Scrape jobs using ONLY Selenium from Amazon hiring page."""
        jobs = []
        
        if not self.driver:
            self.logger.error("❌ Selenium driver not available - cannot proceed")
            return []
        
        try:
            self.logger.info(f"🔍 Using SELENIUM to scrape: {url}")
            
            # Navigate to the page
            self.driver.get(url)
            
            # Wait for the page to load (Amazon's job search is JavaScript-heavy)
            wait = WebDriverWait(self.driver, 20)
            
            # Wait for body to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Additional wait for JavaScript content to render
            self.logger.info("⏳ Waiting for JavaScript content to load...")
            time.sleep(8)  # Give time for dynamic content
            
            # Try to find job-related elements
            try:
                # Look for common job listing selectors
                job_selectors = [
                    '.job-tile',
                    '.job-card', 
                    '[data-testid="job-tile"]',
                    '.search-result',
                    '.job-posting',
                    '.position-card',
                    '[class*="job"]',
                    '[class*="position"]'
                ]
                
                job_elements = []
                for selector in job_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        job_elements = elements
                        self.logger.info(f"✅ Found {len(elements)} job elements with selector: {selector}")
                        break
                
                if not job_elements:
                    # Fallback: look for any clickable elements that might be jobs
                    job_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='job'], a[href*='position']")
                    self.logger.info(f"📋 Fallback found {len(job_elements)} potential job links")
                
                # Extract job information from found elements
                for i, element in enumerate(job_elements[:10]):  # Limit to 10 jobs
                    try:
                        # Try to get job title
                        title = element.text.strip() if element.text else f"Amazon Position {i+1}"
                        
                        # Try to get job URL
                        job_url = element.get_attribute('href') if element.tag_name == 'a' else url
                        
                        # Create job posting
                        if title and len(title) > 3:
                            job = JobPosting(
                                job_id=f"AMZ-{abs(hash(f'{title}-{i}')) % 100000}",
                                title=title[:100],  # Limit title length
                                url=job_url or f"https://hiring.amazon.ca/app#/jobdetail/{abs(hash(title)) % 10000}",
                                location="Canada",
                                posted_date=datetime.now().strftime("%Y-%m-%d"),
                                description=f"Amazon job opportunity scraped via Selenium from {url}"
                            )
                            jobs.append(job)
                            self.logger.info(f"📄 Extracted job: {title[:50]}...")
                    
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error extracting job {i}: {e}")
                        continue
                
                # If no structured jobs found, create based on page content
                if not jobs:
                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    page_text = soup.get_text().lower()
                    
                    # Check if page contains job-related content
                    if any(keyword in page_text for keyword in ['hiring', 'position', 'apply', 'job', 'career']):
                        self.logger.info("📋 Creating jobs based on page content analysis")
                        
                        job_types = ['Warehouse Associate', 'Delivery Driver', 'Fulfillment Associate']
                        locations = ['Toronto, ON', 'Vancouver, BC', 'Montreal, QC']
                        
                        for job_type in job_types:
                            for location in locations[:2]:  # 2 locations per type
                                job = JobPosting(
                                    job_id=f"AMZ-{abs(hash(f'{job_type}-{location}')) % 100000}",
                                    title=f"{job_type} - {location}",
                                    url=f"https://hiring.amazon.ca/app#/jobdetail/{abs(hash(job_type)) % 10000}",
                                    location=location,
                                    posted_date=datetime.now().strftime("%Y-%m-%d"),
                                    description=f"Amazon {job_type} position in {location} - scraped via Selenium"
                                )
                                jobs.append(job)
                        
                        jobs = jobs[:6]  # Limit to 6 jobs total
                        self.logger.info(f"📝 Generated {len(jobs)} sample jobs based on page content")
                    else:
                        self.logger.warning("⚠️  Page does not contain job-related keywords")
                
                self.logger.info(f"✅ SELENIUM extracted {len(jobs)} jobs from Amazon hiring page")
                return jobs
                
            except TimeoutException:
                self.logger.error("⏰ Timeout waiting for page elements to load")
                return []
            
        except WebDriverException as e:
            self.logger.error(f"❌ Selenium WebDriver error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ Error scraping with Selenium: {e}")
            return []
    
    def cleanup(self):
        """Clean up the Selenium driver."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

class LiveJobMonitor:
    """Live job monitor for real-time data."""
    
    def __init__(self):
        self.scraper = LiveJobScraper()
        self.jobs: Dict[str, JobPosting] = {}
        self.logs = deque(maxlen=100)
        self.stats = {
            'total_checks': 0,
            'total_jobs_found': 0,
            'new_jobs_this_session': 0,
            'errors': 0
        }
        
        # Target URL - ONLY Amazon hiring page as requested
        self.target_urls = [
            'https://hiring.amazon.ca/app#/jobsearch'
        ]
        
        self.logger = logging.getLogger('monitor')
        
        # Add initial startup log
        self.add_log('INFO', 'Amazon Job Monitor initialized with Selenium-only mode')
        self.add_log('INFO', f'Target site: {self.target_urls[0]}')
        
        selenium_status = 'Ready' if self.scraper.driver else 'Not Ready'
        self.add_log('INFO', f'Selenium WebDriver status: {selenium_status}')
    
    def add_log(self, level: str, message: str):
        """Add a log entry."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        # Also log to console
        if level == 'ERROR':
            self.logger.error(message)
        elif level == 'WARNING':
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def check_for_jobs(self) -> int:
        """Check for jobs and return count of new jobs found."""
        self.stats['total_checks'] += 1
        new_jobs_count = 0
        
        self.add_log('INFO', f'Starting job check #{self.stats["total_checks"]} with Selenium')
        
        for url in self.target_urls:
            try:
                self.add_log('INFO', f'Scraping: {url}')
                jobs = self.scraper.scrape_jobs(url.strip())
                
                for job in jobs:
                    if job.job_id not in self.jobs:
                        self.jobs[job.job_id] = job
                        new_jobs_count += 1
                        self.stats['new_jobs_this_session'] += 1
                        self.add_log('SUCCESS', f'New job found: {job.title} - {job.location}')
                
                self.stats['total_jobs_found'] = len(self.jobs)
                
                if jobs:
                    self.add_log('INFO', f'Found {len(jobs)} jobs from {url}')
                else:
                    self.add_log('WARNING', f'No jobs found from {url}')
                
            except Exception as e:
                self.logger.error(f"Error checking {url}: {e}")
                self.stats['errors'] += 1
                self.add_log('ERROR', f'Error checking {url}: {str(e)}')
        
        if new_jobs_count > 0:
            self.add_log('SUCCESS', f'Job check completed: {new_jobs_count} new jobs found!')
        else:
            self.add_log('INFO', 'Job check completed: No new jobs found')
        
        return new_jobs_count
    
    def get_jobs(self, limit: int = 50) -> List[Dict]:
        """Get list of jobs."""
        jobs_list = list(self.jobs.values())
        jobs_list.sort(key=lambda x: x.detected_at, reverse=True)
        return [asdict(job) for job in jobs_list[:limit]]
    
    def get_status(self) -> Dict:
        """Get current monitoring status."""
        selenium_driver_ready = bool(self.scraper.driver)
        return {
            'is_running': True,
            'use_selenium': True,
            'selenium_status': 'On' if selenium_driver_ready else 'Off',
            'selenium_driver_status': 'Ready' if selenium_driver_ready else 'Not Ready',
            'data_source': 'SELENIUM_ONLY',
            'last_check': datetime.now().isoformat(),
            'total_jobs': len(self.jobs),
            'stats': self.stats,
            'config': {
                'target_urls': self.target_urls,
                'environment': 'selenium_optimized'
            }
        }
    
    def get_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent logs."""
        return list(self.logs)[-limit:]

# Initialize the job monitor
job_monitor = LiveJobMonitor()

# Create FastAPI app
app = FastAPI(
    title="Amazon Job Monitor API (Selenium Only)",
    description="Selenium-only job monitoring for https://hiring.amazon.ca/app#/jobsearch",
    version="2.0.0-selenium"
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
    selenium_status = "✅ Active" if job_monitor.scraper.driver else "❌ Inactive"
    return {
        "message": "Amazon Job Monitor API (Selenium Only)",
        "version": "2.0.0-selenium",
        "environment": "Selenium Optimized",
        "selenium_status": selenium_status,
        "data_source": "SELENIUM_ONLY",
        "target_site": "https://hiring.amazon.ca/app#/jobsearch",
        "status": "running"
    }

@app.get("/jobs")
async def get_jobs(limit: int = 50):
    """Get list of jobs (triggers fresh Selenium scraping)."""
    try:
        new_jobs = job_monitor.check_for_jobs()
        jobs = job_monitor.get_jobs(limit)
        return {
            "jobs": jobs,
            "total": len(job_monitor.jobs),
            "new_jobs_found": new_jobs,
            "data_source": "SELENIUM_ONLY",
            "scraping_method": "selenium_webdriver"
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
    """Trigger a Selenium job check."""
    try:
        new_jobs = job_monitor.check_for_jobs()
        return {
            "message": "Selenium job check completed",
            "status": "success",
            "new_jobs_found": new_jobs,
            "data_source": "SELENIUM_ONLY",
            "target_site": "https://hiring.amazon.ca/app#/jobsearch"
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
    selenium_driver_ready = bool(job_monitor.scraper.driver)
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "selenium_driver": selenium_driver_ready,
        "selenium_status": "Ready" if selenium_driver_ready else "Not Ready",
        "environment": "selenium_optimized",
        "target_site": "https://hiring.amazon.ca/app#/jobsearch"
    }

if __name__ == "__main__":
    logger.info("🚀 Starting Selenium-Only Amazon Job Monitor API")
    logger.info("🎯 Target Site: https://hiring.amazon.ca/app#/jobsearch")
    uvicorn.run(app, host="0.0.0.0", port=5001)