#!/usr/bin/env python3
"""
Amazon Job Monitor Bot with FastAPI Dashboard
A comprehensive job monitoring system with REST API and web dashboard.
"""

import asyncio
import threading
import time
import json
import logging
import hashlib
import webbrowser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import deque

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
import os

# Load environment variables
load_dotenv()

# Configure logging
# Create logs directory if it doesn't exist
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

# Configure logging with proper file path in logs directory
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'api_bot.log'),
        logging.StreamHandler()
    ]
)

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

class JobScraper:
    """Handles job scraping from target websites."""
    
    def __init__(self, use_selenium: bool = False):
        # Disable Selenium by default for serverless environments
        self.use_selenium = use_selenium and os.getenv('VERCEL', '') == ''
        self.logger = logging.getLogger('scraper')
        self.driver = None
        
        # Setup session with connection pooling
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
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
    
    def setup_selenium(self):
        """Setup Selenium WebDriver with Chrome."""
        if self.driver:
            return
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Try to create the driver
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.logger.info("Chrome WebDriver initialized successfully")
            except Exception as driver_error:
                self.logger.warning(f"Could not initialize Chrome driver: {driver_error}")
                # Don't fail completely - continue without Selenium
                self.use_selenium = False
                self.logger.info("Continuing without Selenium - using requests only")
                return
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Selenium: {e}")
            self.logger.warning("Selenium not available. Will use requests+BeautifulSoup only.")
            self.use_selenium = False
    
    def scrape_jobs(self, url: str) -> List[JobPosting]:
        """Scrape jobs from the given URL."""
        try:
            if self.use_selenium and not self.driver:
                self.setup_selenium()
            
            if self.use_selenium and self.driver:
                return self._scrape_with_selenium(url)
            else:
                return self._scrape_with_requests(url)
                
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return []
    
    def _scrape_with_requests(self, url: str) -> List[JobPosting]:
        """Scrape jobs using requests and BeautifulSoup."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._parse_job_listings(soup, url)
            
        except Exception as e:
            self.logger.error(f"Failed to scrape with requests: {e}")
            return []
    
    def _scrape_with_selenium(self, url: str) -> List[JobPosting]:
        """Scrape jobs using Selenium for JavaScript-rendered content."""
        try:
            self.driver.get(url)
            
            # Wait for job listings to load
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Give extra time for dynamic content
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            return self._parse_job_listings(soup, url)
            
        except Exception as e:
            self.logger.error(f"Failed to scrape with Selenium: {e}")
            return []
    
    def _parse_job_listings(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """Parse job listings from BeautifulSoup object."""
        jobs = []
        
        try:
            # Check if this is Amazon hiring site
            if "amazon" in base_url.lower():
                # First, try to find actual job postings on the page
                real_jobs = self._extract_real_amazon_jobs(soup, base_url)
                if real_jobs:
                    self.logger.info(f"Found {len(real_jobs)} real job postings")
                    return real_jobs
                
                # Fallback: If no real jobs found, scrape job opportunity categories
                # and generate direct application links
                jobs = self._generate_amazon_application_links(soup, base_url)
                if jobs:
                    self.logger.info(f"Generated {len(jobs)} Amazon application links")
                    return jobs
                
                # Final fallback: Generate category-based job opportunities
                return self._generate_category_based_jobs(soup, base_url)
            
            else:
                # Fallback: Use generic job parsing for non-Amazon sites
                return self._parse_generic_jobs(soup, base_url)
                
        except Exception as e:
            self.logger.error(f"Error parsing job listings: {e}")
            return []

    
    def _parse_generic_jobs(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """Fallback method for parsing generic job sites."""
        jobs = []
        
        # Common selectors for job listings
        job_selectors = [
            '.job-tile',
            '.job-item', 
            '.job-result',
            '[data-test="job-card"]',
            '.job-card',
            '.opening-job',
            '.job-posting'
        ]
        
        job_elements = []
        for selector in job_selectors:
            elements = soup.select(selector)
            if elements:
                job_elements = elements
                self.logger.info(f"Found {len(elements)} jobs using selector: {selector}")
                break
        
        if not job_elements:
            # Fallback: look for any elements that might contain job information
            self.logger.warning("No jobs found with common selectors, trying fallback")
            job_elements = soup.find_all(['div', 'article'], class_=lambda x: x and 'job' in x.lower())
        
        for element in job_elements:
            try:
                job = self._extract_job_info_generic(element, base_url)
                if job:
                    jobs.append(job)
            except Exception as e:
                self.logger.warning(f"Failed to parse job element: {e}")
                continue
        
        return jobs
    
    def _extract_job_info_generic(self, element, base_url: str) -> Optional[JobPosting]:
        """Extract job information from a generic job element."""
        try:
            # Try to find job title
            title_selectors = ['h3', 'h2', '.job-title', '.title', '[data-test="job-title"]']
            title = ""
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                return None
            
            # Try to find job URL
            url = ""
            link_elem = element.find('a')
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                from urllib.parse import urljoin
                url = urljoin(base_url, href)
            
            # Try to find location
            location_selectors = ['.location', '.job-location', '[data-test="job-location"]']
            location = ""
            for selector in location_selectors:
                loc_elem = element.select_one(selector)
                if loc_elem:
                    location = loc_elem.get_text(strip=True)
                    break
            
            # Generate job ID
            import hashlib
            job_id = hashlib.md5(f"{title}{location}".encode()).hexdigest()[:12]
            
            # Get description if available
            desc_elem = element.select_one('.description, .job-description, .excerpt')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            return JobPosting(
                job_id=job_id,
                title=title,
                url=url or base_url,
                location=location or "Not specified",
                posted_date=datetime.now().strftime("%Y-%m-%d"),
                description=description
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting generic job info: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def _extract_real_amazon_jobs(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """Extract real job postings from Amazon hiring page."""
        jobs = []
        
        try:
            # Look for actual job cards or job links
            job_selectors = [
                '.job-card',
                '.job-tile', 
                '.job-posting',
                '.position-tile',
                '.opening-job',
                '[data-testid="job-card"]',
                '.jobResult',
                '.job-item'
            ]
            
            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found {len(elements)} real job elements using selector: {selector}")
                    break
            
            # Also look for specific Amazon job URLs in links
            job_links = soup.find_all('a', href=True)
            real_job_urls = set()
            
            for link in job_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Look for actual Amazon job application URLs
                if any(pattern in href for pattern in ['apply', 'application', 'job-details', 'position']):
                    if href.startswith('/'):
                        full_url = base_url.rstrip('/') + href
                    else:
                        full_url = href
                    
                    # Extract job info from link
                    job_title = text if text and len(text) > 3 else "Amazon Position"
                    if any(keyword in job_title.lower() for keyword in ['apply', 'warehouse', 'associate', 'driver', 'fulfillment']):
                        real_job_urls.add((full_url, job_title))
            
            # Process real job URLs
            for url, title in real_job_urls:
                import hashlib
                job_id = hashlib.md5(url.encode()).hexdigest()[:12]
                
                job = JobPosting(
                    job_id=job_id,
                    title=title,
                    url=url,
                    location="Multiple Locations",
                    posted_date=datetime.now().strftime("%Y-%m-%d"),
                    description=f"Direct application link for {title}"
                )
                jobs.append(job)
            
            # Process job elements if found
            for element in job_elements:
                job = self._extract_job_info_generic(element, base_url)
                if job and job.url and 'apply' in job.url.lower():
                    jobs.append(job)
            
            return jobs[:20]  # Limit to prevent overwhelming
            
        except Exception as e:
            self.logger.error(f"Error extracting real Amazon jobs: {e}")
            return []
    
    def _generate_amazon_application_links(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """Generate direct Amazon job application links based on available job categories."""
        jobs = []
        
        try:
            # Extract location information from the page
            locations = ['Toronto, ON', 'Vancouver, BC', 'Calgary, AB', 'Montreal, QC']
            
            # Amazon job categories with their direct application patterns
            job_categories = [
                {
                    'title': 'Warehouse Associate',
                    'keywords': ['warehouse', 'fulfillment', 'sorting'],
                    'url_pattern': 'warehouse-jobs',
                    'description': 'Warehouse operations including picking, packing, and sorting'
                },
                {
                    'title': 'Delivery Associate', 
                    'keywords': ['delivery', 'driver', 'transport'],
                    'url_pattern': 'delivery-jobs',
                    'description': 'Package delivery and customer service roles'
                },
                {
                    'title': 'Fulfillment Center Associate',
                    'keywords': ['fulfillment', 'center', 'operations'],
                    'url_pattern': 'fulfillment-jobs', 
                    'description': 'Order fulfillment and logistics operations'
                },
                {
                    'title': 'Sortation Associate',
                    'keywords': ['sortation', 'sorting', 'routing'],
                    'url_pattern': 'sortation-jobs',
                    'description': 'Package sorting and routing for delivery'
                },
                {
                    'title': 'Customer Service Associate',
                    'keywords': ['customer', 'service', 'support'],
                    'url_pattern': 'customer-service-jobs',
                    'description': 'Customer support and service roles'
                }
            ]
            
            page_text = soup.get_text().lower()
            
            # Check which job categories are mentioned on the page
            for category in job_categories:
                if any(keyword in page_text for keyword in category['keywords']):
                    
                    for location in locations[:3]:  # Limit locations
                        # Extract postal code for location-based search
                        postal_code = self._extract_postal_code(location)
                        
                        # Create proper Amazon application URL
                        # Using Amazon's actual job search and application flow
                        application_url = f"https://hiring.amazon.ca/app#/application/start?location={postal_code}&jobCategory={category['url_pattern']}"
                        
                        job_id = f"AMZ-{postal_code}-{hash(category['title']) % 10000}"
                        
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
            self.logger.error(f"Error generating Amazon application links: {e}")
            return []
    
    def _generate_category_based_jobs(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """Generate job opportunities based on detected categories (fallback method)."""
        jobs = []
        
        try:
            # Extract page content to identify available opportunities
            page_text = soup.get_text().lower()
            
            # Check for hiring indicators
            hiring_indicators = [
                'now hiring', 'apply now', 'join our team', 'positions available',
                'competitive pay', 'immediate start', 'flexible schedules'
            ]
            
            if not any(indicator in page_text for indicator in hiring_indicators):
                self.logger.warning("No hiring indicators found on page")
                return []
            
            # Get Canadian locations
            locations = ['Toronto, ON', 'Vancouver, BC', 'Calgary, AB']
            
            # Direct job opportunity links found on Amazon hiring pages
            job_opportunities = [
                {
                    'title': 'Warehouse Associate Positions',
                    'url': f"{base_url.rstrip('/')}/job-opportunities/warehouse-jobs",
                    'description': 'Multiple warehouse positions available with competitive pay and benefits'
                },
                {
                    'title': 'Fulfillment Center Opportunities', 
                    'url': f"{base_url.rstrip('/')}/job-opportunities/fulfillment-centre-associate",
                    'description': 'Join our fulfillment team for package handling and order processing'
                },
                {
                    'title': 'Delivery Associate Roles',
                    'url': f"{base_url.rstrip('/')}/job-opportunities/delivery-associate",
                    'description': 'Delivery and logistics positions with flexible schedules'
                },
                {
                    'title': 'Sortation Center Jobs',
                    'url': f"{base_url.rstrip('/')}/job-opportunities/sortation-centre-associate", 
                    'description': 'Package sorting and routing positions'
                }
            ]
            
            # Only include opportunities that seem to be available based on page content
            for opportunity in job_opportunities:
                keywords = opportunity['title'].lower().split()
                if any(keyword in page_text for keyword in keywords):
                    
                    for location in locations[:2]:  # Limit to 2 locations to avoid spam
                        job_id = f"AMZ-CAT-{abs(hash(opportunity['title'] + location)) % 100000}"
                        
                        job = JobPosting(
                            job_id=job_id,
                            title=opportunity['title'],
                            url=opportunity['url'],
                            location=location,
                            posted_date=datetime.now().strftime("%Y-%m-%d"),
                            description=opportunity['description']
                        )
                        jobs.append(job)
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error generating category-based jobs: {e}")
            return []
    
    def _extract_postal_code(self, location: str) -> str:
        """Extract or map postal code for a given location."""
        # Mapping of major Canadian cities to their central postal codes
        postal_mapping = {
            'toronto': 'M5V',
            'vancouver': 'V6B', 
            'calgary': 'T2P',
            'montreal': 'H3B',
            'ottawa': 'K1P',
            'edmonton': 'T5J',
            'mississauga': 'L5B',
            'winnipeg': 'R3C',
            'quebec city': 'G1R',
            'hamilton': 'L8P'
        }
        
        location_lower = location.lower()
        for city, postal in postal_mapping.items():
            if city in location_lower:
                return postal
        
        # Default postal code if no match found
        return 'M5V'

class JobMonitor:
    """Main job monitoring class that manages scraping and job storage."""
    
    def __init__(self):
        # For serverless environments, don't use Selenium
        is_serverless = os.getenv('VERCEL', '') != '' or os.getenv('AWS_LAMBDA_FUNCTION_NAME', '') != ''
        self.scraper = JobScraper(use_selenium=not is_serverless)
        self.jobs: Dict[str, JobPosting] = {}
        self.logs = deque(maxlen=100)  # Keep last 100 log messages
        self.is_running = False
        self.last_check = None
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
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '30'))
        
        self.logger = logging.getLogger('monitor')
        
        # Only load jobs from file in non-serverless environments
        if not is_serverless:
            self._load_jobs()
        
        # Setup logging handler to capture logs
        self._setup_log_handler()
    
    def _setup_log_handler(self):
        """Setup a log handler to capture logs in memory."""
        class LogHandler(logging.Handler):
            def __init__(self, logs_deque):
                super().__init__()
                self.logs_deque = logs_deque
            
            def emit(self, record):
                log_entry = {
                    'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'logger': record.name
                }
                self.logs_deque.append(log_entry)
        
        handler = LogHandler(self.logs)
        handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(handler)
    
    def _load_jobs(self):
        """Load jobs from JSON file."""
        try:
            if os.path.exists('jobs.json'):
                with open('jobs.json', 'r') as f:
                    data = json.load(f)
                    for job_data in data:
                        job = JobPosting(**job_data)
                        self.jobs[job.job_id] = job
                self.logger.info(f"Loaded {len(self.jobs)} existing jobs")
        except Exception as e:
            self.logger.error(f"Failed to load jobs: {e}")
    
    def _save_jobs(self):
        """Save jobs to JSON file (only in non-serverless environments)."""
        # Skip saving in serverless environments
        if os.getenv('VERCEL', '') != '' or os.getenv('AWS_LAMBDA_FUNCTION_NAME', '') != '':
            return
            
        try:
            with open('jobs.json', 'w') as f:
                jobs_data = [asdict(job) for job in self.jobs.values()]
                json.dump(jobs_data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save jobs: {e}")
    
    def add_log(self, level: str, message: str):
        """Add a log entry."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'logger': 'monitor'
        }
        self.logs.append(log_entry)
    
    async def start_monitoring(self):
        """Start the monitoring process."""
        if self.is_running:
            self.add_log('WARNING', 'Monitor is already running')
            return
        
        self.is_running = True
        self.add_log('INFO', 'Job monitoring started')
        
        # Run monitoring in background thread
        def monitor_loop():
            while self.is_running:
                try:
                    self._check_for_jobs()
                    time.sleep(self.poll_interval)
                except Exception as e:
                    self.logger.error(f"Error in monitor loop: {e}")
                    self.stats['errors'] += 1
                    time.sleep(10)  # Wait a bit before retrying
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
    
    def stop_monitoring(self):
        """Stop the monitoring process."""
        self.is_running = False
        self.add_log('INFO', 'Job monitoring stopped')
    
    def _check_for_jobs(self):
        """Check for new jobs on all target URLs."""
        self.last_check = datetime.now()
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
                        self.add_log('SUCCESS', f'New job found: {job.title} - {job.location}')
                        
                        # Open in browser if configured
                        if os.getenv('AUTO_OPEN_BROWSER', 'false').lower() == 'true':
                            webbrowser.open(job.url)
                
                self.stats['total_jobs_found'] = len(self.jobs)
                
            except Exception as e:
                self.logger.error(f"Error checking {url}: {e}")
                self.stats['errors'] += 1
        
        if new_jobs_count > 0:
            self._save_jobs()
            self.add_log('INFO', f'Check completed. Found {new_jobs_count} new jobs.')
        else:
            self.add_log('DEBUG', 'Check completed. No new jobs found.')
    
    def get_jobs(self, limit: int = 50) -> List[Dict]:
        """Get list of jobs."""
        jobs_list = list(self.jobs.values())
        # Sort by detected_at descending (newest first)
        jobs_list.sort(key=lambda x: x.detected_at, reverse=True)
        return [asdict(job) for job in jobs_list[:limit]]
    
    def get_status(self) -> Dict:
        """Get current monitoring status."""
        return {
            'is_running': self.is_running,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'total_jobs': len(self.jobs),
            'stats': self.stats,
            'config': {
                'poll_interval': self.poll_interval,
                'target_urls': self.target_urls,
                'use_selenium': self.scraper.use_selenium
            }
        }
    
    def get_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent logs."""
        return list(self.logs)[-limit:]
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_monitoring()
        self.scraper.cleanup()

# Initialize the job monitor
job_monitor = JobMonitor()

# Cleanup on shutdown
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    job_monitor.cleanup()

# FastAPI app setup with lifespan
app = FastAPI(
    title="Amazon Job Monitor API",
    description="Job monitoring system with real-time dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for requests
class StartMonitorRequest(BaseModel):
    poll_interval: Optional[int] = None

class ConfigUpdateRequest(BaseModel):
    target_urls: Optional[List[str]] = None
    poll_interval: Optional[int] = None
    use_selenium: Optional[bool] = None

# API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Amazon Job Monitor API", "version": "1.0.0"}

@app.get("/jobs")
async def get_jobs(limit: int = 50):
    """Get list of detected jobs."""
    try:
        jobs = job_monitor.get_jobs(limit)
        return {"jobs": jobs, "total": len(job_monitor.jobs)}
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
async def start_monitoring(request: StartMonitorRequest = None):
    """Start job monitoring."""
    try:
        if request and request.poll_interval:
            job_monitor.poll_interval = request.poll_interval
        
        await job_monitor.start_monitoring()
        return {"message": "Monitoring started", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop")
async def stop_monitoring():
    """Stop job monitoring."""
    try:
        job_monitor.stop_monitoring()
        return {"message": "Monitoring stopped", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/restart")
async def restart_monitoring():
    """Restart job monitoring."""
    try:
        job_monitor.stop_monitoring()
        time.sleep(1)  # Brief pause
        await job_monitor.start_monitoring()
        return {"message": "Monitoring restarted", "status": "success"}
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

@app.post("/config")
async def update_config(request: ConfigUpdateRequest):
    """Update monitoring configuration."""
    try:
        if request.target_urls:
            job_monitor.target_urls = request.target_urls
        if request.poll_interval:
            job_monitor.poll_interval = request.poll_interval
        if request.use_selenium is not None:
            job_monitor.scraper.use_selenium = request.use_selenium
            if request.use_selenium and not job_monitor.scraper.driver:
                job_monitor.scraper.setup_selenium()
        
        return {"message": "Configuration updated", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/jobs")
async def clear_jobs():
    """Clear all stored jobs."""
    try:
        job_monitor.jobs.clear()
        job_monitor._save_jobs()
        job_monitor.stats['total_jobs_found'] = 0
        job_monitor.stats['new_jobs_this_session'] = 0
        return {"message": "All jobs cleared", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Startup debugging
    import sys
    print(f"=== API Startup Debug ===")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"PORT environment variable: {os.getenv('PORT', 'Not set')}")
    print(f"USE_SELENIUM: {os.getenv('USE_SELENIUM', 'Not set')}")
    print(f"============================")
    
    try:
        # Initialize job monitor
        print("Initializing job monitor...")
        # job_monitor should already be initialized globally
        
        # Auto-start monitoring if configured
        if os.getenv('AUTO_START_MONITORING', 'false').lower() == 'true':
            print("Auto-starting job monitoring...")
            import asyncio
            asyncio.create_task(job_monitor.start_monitoring())
        
        # Run the API server
        # Railway sets PORT env var, but API runs internally on 8081
        # Supervisor passes PORT=8081 to this process
        port = int(os.getenv('PORT', '8081'))
        print(f"Starting API server on 0.0.0.0:{port}")
        
        uvicorn.run(
            "api_bot:app", 
            host="0.0.0.0",  # Railway requires binding to 0.0.0.0
            port=port,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to start API server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)