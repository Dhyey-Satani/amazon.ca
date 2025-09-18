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
            # Only extract real job postings - no fake data generation
            if "amazon" in base_url.lower():
                real_jobs = self._extract_real_amazon_jobs(soup, base_url)
                if real_jobs:
                    self.logger.info(f"Found {len(real_jobs)} real job postings")
                    return real_jobs
                else:
                    self.logger.info("No real job postings found on Amazon page")
                    return []
            else:
                # Use generic job parsing for non-Amazon sites
                return self._parse_generic_jobs(soup, base_url)
                
        except Exception as e:
            self.logger.error(f"Error parsing job listings: {e}")
            return []
    
    def _extract_canadian_locations(self, soup: BeautifulSoup) -> List[str]:
        """Extract Canadian locations from the page - for real job parsing only."""
        locations = set()
        page_text = soup.get_text()
        
        # Only extract locations that are explicitly mentioned in job postings
        # Look for patterns like "Location: Toronto, ON" or "Based in Vancouver, BC"
        import re
        location_patterns = [
            r'location[:\s]+([^\n\r]+(?:ON|BC|AB|QC|MB|SK|NS|NB|PE|NL|NT|YT|NU))',
            r'based in[:\s]+([^\n\r]+(?:ON|BC|AB|QC|MB|SK|NS|NB|PE|NL|NT|YT|NU))',
            r'work from[:\s]+([^\n\r]+(?:ON|BC|AB|QC|MB|SK|NS|NB|PE|NL|NT|YT|NU))'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                clean_location = match.strip().replace('\n', '').replace('\r', '')
                if len(clean_location) < 50:  # Reasonable location length
                    locations.add(clean_location)
        
        return list(locations)[:5]  # Limit to 5 real locations
    
    def _extract_real_amazon_jobs(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """Extract ONLY real job postings from Amazon hiring page - no fake data."""
        jobs = []
        
        try:
            # Look for actual job cards or job links with strict criteria
            job_selectors = [
                '.job-card',
                '.job-tile', 
                '.job-posting',
                '.position-tile',
                '.opening-job',
                '[data-testid="job-card"]',
                '.jobResult',
                '.job-item',
                '[class*="job"][class*="card"]',
                '[class*="position"][class*="card"]'
            ]
            
            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found {len(elements)} potential job elements using selector: {selector}")
                    break
            
            # Only look for genuine Amazon job application URLs in links
            job_links = soup.find_all('a', href=True)
            real_job_urls = set()
            
            for link in job_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # STRICT criteria: Only accept URLs that are clearly job applications
                if (any(pattern in href for pattern in ['/job/', '/position/', '/apply/', '/application/']) and 
                    any(domain in href for domain in ['amazon.ca', 'amazon.com']) and
                    text and len(text) > 5 and 
                    any(keyword in text.lower() for keyword in ['apply', 'position', 'job', 'role'])):
                    
                    if href.startswith('/'):
                        full_url = base_url.rstrip('/') + href
                    else:
                        full_url = href
                    
                    # Only include if it's a legitimate job title
                    if (len(text) > 5 and 
                        not any(skip in text.lower() for skip in ['home', 'about', 'contact', 'help', 'support']) and
                        any(job_word in text.lower() for job_word in ['associate', 'driver', 'operator', 'specialist', 'manager', 'coordinator'])):
                        real_job_urls.add((full_url, text))
            
            # Process real job URLs with strict validation
            for url, title in real_job_urls:
                # Additional validation: URL must contain job-related parameters or paths
                if (('/job' in url.lower() or '/position' in url.lower() or '/apply' in url.lower()) and
                    'amazon' in url.lower()):
                    
                    job_id = hashlib.md5(url.encode()).hexdigest()[:12]
                    
                    job = JobPosting(
                        job_id=job_id,
                        title=title,
                        url=url,
                        location="Location TBD",  # Will be determined from actual job page
                        posted_date=datetime.now().strftime("%Y-%m-%d"),
                        description=f"Real Amazon job posting: {title}"
                    )
                    jobs.append(job)
            
            # Process job elements if found (with strict validation)
            for element in job_elements:
                job = self.extract_job_info(element, base_url)
                if (job and job.url and 
                    ('amazon' in job.url.lower()) and 
                    ('/job' in job.url.lower() or '/position' in job.url.lower() or '/apply' in job.url.lower())):
                    jobs.append(job)
            
            # Remove duplicates and limit results
            seen_urls = set()
            unique_jobs = []
            for job in jobs:
                if job.url not in seen_urls:
                    seen_urls.add(job.url)
                    unique_jobs.append(job)
            
            self.logger.info(f"Extracted {len(unique_jobs)} verified real job postings")
            return unique_jobs[:10]  # Limit to top 10 most relevant
            
        except Exception as e:
            self.logger.error(f"Error extracting real Amazon jobs: {e}")
            return []
    
    def _generate_amazon_application_links(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """REMOVED: This method no longer generates fake job data."""
        self.logger.info("Fake job generation disabled - returning empty list")
        return []
    
    def _generate_category_based_jobs(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """REMOVED: This method no longer generates fake job data."""
        self.logger.info("Fake job generation disabled - returning empty list")
        return []
    
    def _extract_postal_code(self, location: str) -> str:
        """REMOVED: This method was used for fake data generation."""
        # This method is no longer needed since we don't generate fake jobs
        return ""
    
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
            'urls': os.getenv('AMAZON_URLS', 'https://hiring.amazon.ca/app#/jobsearch').split(','),
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
                        self.logger.info(f"Found {len(jobs)} real job postings from {url}")
                        break
                    else:
                        self.logger.info(f"No real job postings found at {url} (attempt {retry_count + 1}). Fake data generation has been disabled.")
                    
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
                    self.logger.info(f"New REAL job found: {job.title} - {job.location} - {job.url}")
                    self.notifications.notify_new_job(job)
                    new_jobs_count += 1
                    self.stats['new_jobs'] += 1
        
        if new_jobs_count == 0:
            self.logger.info("✅ No fake data generated. Only real job postings are returned.")
        
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