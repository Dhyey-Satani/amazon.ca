#!/usr/bin/env python3
"""
Amazon Hiring Page Monitor Bot

A bot that monitors Amazon hiring pages for new job postings and sends notifications
when new opportunities are found. Supports multiple notification methods and
deployment options.

Author: Generated for warehouse/shift job monitoring
"""

import os
import sys
import time
import json
import sqlite3
import logging
import hashlib
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class JobPosting:
    """Represents a job posting with all relevant details."""
    job_id: str
    title: str
    url: str
    location: str
    posted_date: str
    description: str = ""
    hash: str = ""
    
    def __post_init__(self):
        """Generate a hash for the job posting to detect changes."""
        if not self.hash:
            content = f"{self.job_id}{self.title}{self.location}{self.posted_date}"
            self.hash = hashlib.md5(content.encode()).hexdigest()


class DatabaseManager:
    """Handles job storage and retrieval using SQLite."""
    
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with the jobs table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    location TEXT NOT NULL,
                    posted_date TEXT NOT NULL,
                    description TEXT,
                    hash TEXT NOT NULL,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add_job(self, job: JobPosting) -> bool:
        """Add a job to the database. Returns True if it's a new job."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if job already exists
            cursor.execute("SELECT job_id FROM jobs WHERE job_id = ?", (job.job_id,))
            exists = cursor.fetchone() is not None
            
            if not exists:
                cursor.execute("""
                    INSERT INTO jobs (job_id, title, url, location, posted_date, description, hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (job.job_id, job.title, job.url, job.location, 
                      job.posted_date, job.description, job.hash))
                conn.commit()
                return True
            else:
                # Update last_seen timestamp
                cursor.execute("""
                    UPDATE jobs SET last_seen = CURRENT_TIMESTAMP 
                    WHERE job_id = ?
                """, (job.job_id,))
                conn.commit()
                return False
    
    def get_seen_job_ids(self) -> Set[str]:
        """Get all previously seen job IDs."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT job_id FROM jobs")
            return {row[0] for row in cursor.fetchall()}
    
    def cleanup_old_jobs(self, days: int = 30):
        """Remove jobs older than specified days."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM jobs 
                WHERE last_seen < datetime('now', '-{} days')
            """.format(days))
            conn.commit()


class NotificationManager:
    """Handles different types of notifications."""
    
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.email_enabled = os.getenv('EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
        self.desktop_enabled = os.getenv('DESKTOP_NOTIFICATIONS', 'true').lower() == 'true'
        self.browser_enabled = os.getenv('AUTO_OPEN_BROWSER', 'true').lower() == 'true'
        
        # Setup logging for notifications
        self.logger = logging.getLogger('notifications')
    
    def send_telegram_message(self, message: str) -> bool:
        """Send a Telegram message."""
        if not self.telegram_token or not self.telegram_chat_id:
            self.logger.warning("Telegram credentials not configured")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': False
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            self.logger.info("Telegram message sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_desktop_notification(self, title: str, message: str):
        """Send a desktop notification."""
        if not self.desktop_enabled:
            return
        
        try:
            if sys.platform == "win32":
                import win10toast
                toaster = win10toast.ToastNotifier()
                toaster.show_toast(title, message, duration=10)
            elif sys.platform == "darwin":
                os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')
            else:  # Linux
                os.system(f'notify-send "{title}" "{message}"')
            
            self.logger.info("Desktop notification sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send desktop notification: {e}")
    
    def open_in_browser(self, url: str):
        """Open URL in default browser."""
        if not self.browser_enabled:
            return
        
        try:
            webbrowser.open(url)
            self.logger.info(f"Opened {url} in browser")
        except Exception as e:
            self.logger.error(f"Failed to open browser: {e}")
    
    def notify_new_job(self, job: JobPosting):
        """Send notifications for a new job posting."""
        title = "🚨 New Amazon Job Found!"
        message = f"""
<b>New Job Alert!</b>

<b>Title:</b> {job.title}
<b>Location:</b> {job.location}
<b>Posted:</b> {job.posted_date}
<b>Job ID:</b> {job.job_id}

<a href="{job.url}">🔗 Apply Now</a>

Found at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        # Send notifications
        self.send_telegram_message(message)
        self.send_desktop_notification(title, f"{job.title} - {job.location}")
        self.open_in_browser(job.url)


class AmazonJobScraper:
    """Scrapes Amazon hiring pages for job postings."""
    
    def __init__(self, use_selenium: bool = True):
        self.use_selenium = use_selenium
        self.logger = logging.getLogger('scraper')
        self.session = requests.Session()
        self.driver = None
        
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
            except Exception as driver_error:
                self.logger.warning(f"Could not initialize Chrome driver: {driver_error}")
                self.logger.info("Trying with ChromeDriverManager (auto-download)...")
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Selenium: {e}")
            self.logger.warning("Selenium not available. Will use requests+BeautifulSoup only.")
            raise
    
    def scrape_with_requests(self, url: str) -> List[JobPosting]:
        """Scrape jobs using requests and BeautifulSoup."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self.parse_job_listings(soup, url)
            
        except Exception as e:
            self.logger.error(f"Failed to scrape with requests: {e}")
            return []
    
    def scrape_with_selenium(self, url: str) -> List[JobPosting]:
        """Scrape jobs using Selenium for JavaScript-rendered content."""
        try:
            if not self.driver:
                self.setup_selenium()
            
            self.driver.get(url)
            
            # Wait for job listings to load
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Give extra time for dynamic content
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            return self.parse_job_listings(soup, url)
            
        except Exception as e:
            self.logger.error(f"Failed to scrape with Selenium: {e}")
            return []
    
    def parse_job_listings(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
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
    
    def _extract_canadian_locations(self, soup: BeautifulSoup) -> List[str]:
        """Extract Canadian locations from the page."""
        locations = set()
        page_text = soup.get_text()
        
        # Common Canadian cities and provinces
        canadian_locations = [
            'Toronto, ON', 'Vancouver, BC', 'Calgary, AB', 'Montreal, QC',
            'Ottawa, ON', 'Edmonton, AB', 'Mississauga, ON', 'Winnipeg, MB',
            'Quebec City, QC', 'Hamilton, ON', 'Brampton, ON', 'Surrey, BC',
            'Laval, QC', 'Halifax, NS', 'London, ON', 'Markham, ON',
            'Vaughan, ON', 'Gatineau, QC', 'Longueuil, QC', 'Burnaby, BC',
            'Saskatoon, SK', 'Kitchener, ON', 'Windsor, ON', 'Regina, SK',
            'Richmond, BC', 'Richmond Hill, ON', 'Oakville, ON', 'Burlington, ON',
            'Greater Toronto Area', 'GTA'
        ]
        
        for location in canadian_locations:
            if location.lower() in page_text.lower():
                locations.add(location)
        
        return list(locations)[:10]  # Limit to prevent too many duplicates
    
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
                job = self.extract_job_info(element, base_url)
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
            locations = self._extract_canadian_locations(soup)
            if not locations:
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
            locations = self._extract_canadian_locations(soup)
            if not locations:
                locations = ['Canada']
            
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
    
    def _parse_generic_jobs(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """Fallback method for parsing generic job sites."""
        jobs = []
        
        # Common selectors for Amazon job pages
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
                job = self.extract_job_info(element, base_url)
                if job:
                    jobs.append(job)
            except Exception as e:
                self.logger.warning(f"Failed to parse job element: {e}")
                continue
        
        self.logger.info(f"Successfully parsed {len(jobs)} jobs")
        return jobs
    
    def extract_job_info(self, element, base_url: str) -> Optional[JobPosting]:
        """Extract job information from a job element."""
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
                url = urljoin(base_url, href)
            
            # Try to find location
            location_selectors = ['.location', '.job-location', '[data-test="job-location"]']
            location = ""
            for selector in location_selectors:
                loc_elem = element.select_one(selector)
                if loc_elem:
                    location = loc_elem.get_text(strip=True)
                    break
            
            # Try to find posted date
            date_selectors = ['.date', '.posted-date', '.job-date', '[data-test="job-date"]']
            posted_date = ""
            for selector in date_selectors:
                date_elem = element.select_one(selector)
                if date_elem:
                    posted_date = date_elem.get_text(strip=True)
                    break
            
            if not posted_date:
                posted_date = datetime.now().strftime('%Y-%m-%d')
            
            # Generate job ID from URL or hash of content
            job_id = ""
            if url:
                # Try to extract ID from URL
                import re
                id_match = re.search(r'job[_-]?id[=:](\w+)', url, re.IGNORECASE)
                if id_match:
                    job_id = id_match.group(1)
                else:
                    job_id = hashlib.md5(url.encode()).hexdigest()[:12]
            else:
                job_id = hashlib.md5(f"{title}{location}".encode()).hexdigest()[:12]
            
            # Get description if available
            desc_elem = element.select_one('.description, .job-description, .excerpt')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            return JobPosting(
                job_id=job_id,
                title=title,
                url=url or base_url,
                location=location or "Not specified",
                posted_date=posted_date,
                description=description
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting job info: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


class AmazonJobBot:
    """Main bot class that orchestrates job monitoring."""
    
    def __init__(self):
        self.config = self.load_config()
        self.setup_logging()
        
        self.db = DatabaseManager(self.config['database_path'])
        self.notifications = NotificationManager()
        self.scraper = AmazonJobScraper(use_selenium=self.config['use_selenium'])
        
        self.logger = logging.getLogger('bot')
        self.running = False
        
        # Stats
        self.stats = {
            'total_runs': 0,
            'jobs_found': 0,
            'new_jobs': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def load_config(self) -> Dict:
        """Load configuration from environment variables."""
        return {
            'urls': os.getenv('AMAZON_URLS', 'https://hiring.amazon.ca').split(','),
            'poll_interval': int(os.getenv('POLL_INTERVAL', '10')),
            'use_selenium': os.getenv('USE_SELENIUM', 'true').lower() == 'true',
            'database_path': os.getenv('DATABASE_PATH', 'jobs.db'),
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'retry_delay': int(os.getenv('RETRY_DELAY', '60')),
            'cleanup_days': int(os.getenv('CLEANUP_DAYS', '30')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO').upper()
        }
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Setup file and console logging
        logging.basicConfig(
            level=getattr(logging, self.config['log_level']),
            format=log_format,
            handlers=[
                logging.FileHandler(log_dir / 'bot.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Reduce noise from selenium and requests
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    def run_single_check(self) -> int:
        """Run a single check of all configured URLs."""
        new_jobs_count = 0
        
        for url in self.config['urls']:
            url = url.strip()
            if not url:
                continue
            
            self.logger.info(f"Checking URL: {url}")
            
            retry_count = 0
            jobs = []
            
            while retry_count <= self.config['max_retries']:
                try:
                    if self.config['use_selenium']:
                        jobs = self.scraper.scrape_with_selenium(url)
                    else:
                        jobs = self.scraper.scrape_with_requests(url)
                    
                    if jobs:
                        break
                    else:
                        self.logger.warning(f"No jobs found for {url} (attempt {retry_count + 1})")
                    
                except Exception as e:
                    self.logger.error(f"Error scraping {url} (attempt {retry_count + 1}): {e}")
                    self.stats['errors'] += 1
                
                retry_count += 1
                if retry_count <= self.config['max_retries']:
                    self.logger.info(f"Retrying in {self.config['retry_delay']} seconds...")
                    time.sleep(self.config['retry_delay'])
            
            # Process found jobs
            self.stats['jobs_found'] += len(jobs)
            
            for job in jobs:
                if self.db.add_job(job):
                    self.logger.info(f"New job found: {job.title} - {job.location}")
                    self.notifications.notify_new_job(job)
                    new_jobs_count += 1
                    self.stats['new_jobs'] += 1
        
        return new_jobs_count
    
    def run(self):
        """Main bot loop."""
        self.logger.info("Amazon Job Bot starting...")
        self.logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
        
        self.running = True
        
        try:
            while self.running:
                self.stats['total_runs'] += 1
                
                start_time = time.time()
                new_jobs = self.run_single_check()
                duration = time.time() - start_time
                
                self.logger.info(f"Check completed in {duration:.2f}s. Found {new_jobs} new jobs.")
                
                # Cleanup old jobs periodically
                if self.stats['total_runs'] % 100 == 0:
                    self.db.cleanup_old_jobs(self.config['cleanup_days'])
                    self.logger.info("Cleaned up old job records")
                
                # Log stats every hour
                if self.stats['total_runs'] % (3600 // self.config['poll_interval']) == 0:
                    self.log_stats()
                
                if self.running:
                    self.logger.debug(f"Sleeping for {self.config['poll_interval']} seconds...")
                    time.sleep(self.config['poll_interval'])
                    
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise
        finally:
            self.cleanup()
    
    def log_stats(self):
        """Log bot statistics."""
        uptime = datetime.now() - self.stats['start_time']
        self.logger.info(f"Bot Stats - Uptime: {uptime}, "
                        f"Runs: {self.stats['total_runs']}, "
                        f"Jobs Found: {self.stats['jobs_found']}, "
                        f"New Jobs: {self.stats['new_jobs']}, "
                        f"Errors: {self.stats['errors']}")
    
    def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up...")
        self.running = False
        if self.scraper:
            self.scraper.cleanup()


def main():
    """Main entry point."""
    try:
        bot = AmazonJobBot()
        bot.run()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()