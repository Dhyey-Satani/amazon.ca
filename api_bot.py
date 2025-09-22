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

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
import os
from collections import defaultdict
from threading import Lock

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
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
    
    def __init__(self, use_selenium: bool = True):
        # Initialize logger first before using it
        self.logger = logging.getLogger('scraper')
        
        # FORCE SELENIUM ONLY - No fallback to requests+BeautifulSoup
        self.logger.info("SELENIUM-ONLY MODE: Forcing Selenium usage for all scraping operations")
        
        # Detect operating system and set appropriate paths
        import platform
        is_windows = platform.system() == 'Windows'
        is_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER', 'false').lower() == 'true'
        
        if is_docker:
            # Docker/Cloud deployment paths
            os.environ['HOME'] = '/app'
            os.environ['XDG_CACHE_HOME'] = '/app/.cache'
            os.environ['WDM_CACHE_DIR'] = '/app/.wdm'
            os.environ['SE_CACHE_PATH'] = '/app/.cache/selenium'
            cache_dirs = ['/app/.cache', '/app/.wdm', '/app/.cache/selenium', '/app/.chrome_user_data']
        elif is_windows:
            # Windows-specific paths
            base_dir = os.path.expanduser('~')
            cache_base = os.path.join(base_dir, '.cache')
            cache_dirs = [
                os.path.join(cache_base, 'selenium'),
                os.path.join(cache_base, 'webdriver'),
                os.path.join(base_dir, '.wdm'),
                os.path.join(base_dir, '.chrome_user_data')
            ]
            
            # Set environment variables for Windows
            os.environ['WDM_CACHE_DIR'] = os.path.join(base_dir, '.wdm')
            os.environ['SE_CACHE_PATH'] = os.path.join(cache_base, 'selenium')
        else:
            # Linux paths (for non-Docker Linux systems)
            base_dir = os.path.expanduser('~')
            cache_dirs = [
                os.path.join(base_dir, '.cache', 'selenium'),
                os.path.join(base_dir, '.wdm'),
                os.path.join(base_dir, '.chrome_user_data')
            ]
            os.environ['WDM_CACHE_DIR'] = os.path.join(base_dir, '.wdm')
            os.environ['SE_CACHE_PATH'] = os.path.join(base_dir, '.cache', 'selenium')
        
        # Create cache directories with proper permissions
        for cache_dir in cache_dirs:
            try:
                os.makedirs(cache_dir, exist_ok=True)
                self.logger.info(f"Created cache directory: {cache_dir}")
            except (PermissionError, OSError) as e:
                self.logger.warning(f"Failed to create cache directory {cache_dir}: {e}")
                # Continue anyway - we'll try to make Selenium work
        
        # FORCE SELENIUM USAGE - No environment variable checks
        self.logger.info(f"SELENIUM FORCED ON for Amazon job scraping on {platform.system()}")
        self.use_selenium = True  # ALWAYS TRUE
        self.driver = None
        
        # Remove requests session setup - we only use Selenium
        self.session = None
        
        # Setup headers for Selenium
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def setup_selenium(self):
        """Setup Selenium WebDriver with Chrome for cross-platform environment."""
        if self.driver:
            return
        
        try:
            import platform
            is_windows = platform.system() == 'Windows'
            is_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER', 'false').lower() == 'true'
            
            chrome_options = Options()
            
            if is_docker:
                # Docker/Cloud environment Chrome options
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-extensions')
                chrome_options.add_argument('--disable-background-timer-throttling')
                chrome_options.add_argument('--disable-backgrounding-occluded-windows')
                chrome_options.add_argument('--disable-renderer-backgrounding')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_argument('--disable-web-security')
                chrome_options.add_argument('--allow-running-insecure-content')
                chrome_options.add_argument('--disable-features=TranslateUI')
                chrome_options.add_argument('--disable-ipc-flooding-protection')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Set user data directory to writable location
                user_data_dir = os.path.join('/app', '.chrome_user_data')
                os.makedirs(user_data_dir, exist_ok=True)
                chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
                
                self.logger.info("Configuring Chrome for Docker/Cloud environment")
            elif is_windows:
                # Windows-specific Chrome options
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-extensions')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_argument('--disable-web-security')
                chrome_options.add_argument('--allow-running-insecure-content')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Set user data directory to user's home on Windows
                import uuid
                unique_id = str(uuid.uuid4())[:8]
                user_data_dir = os.path.join(os.path.expanduser('~'), f'.chrome_user_data_{unique_id}')
                os.makedirs(user_data_dir, exist_ok=True)
                chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
                
                self.logger.info("Configuring Chrome for Windows environment")
            else:
                # Production-optimized Chrome options for Linux/Docker
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-extensions')
                chrome_options.add_argument('--disable-background-timer-throttling')
                chrome_options.add_argument('--disable-backgrounding-occluded-windows')
                chrome_options.add_argument('--disable-renderer-backgrounding')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_argument('--disable-web-security')
                chrome_options.add_argument('--allow-running-insecure-content')
                chrome_options.add_argument('--disable-features=TranslateUI')
                chrome_options.add_argument('--disable-ipc-flooding-protection')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Set user data directory to writable location
                user_data_dir = os.path.join('/app', '.chrome_user_data')
                os.makedirs(user_data_dir, exist_ok=True)
                chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            
            # Try different Chrome binary locations based on OS
            driver_created = False
            
            if is_docker:
                # Docker/Cloud Chrome detection
                chrome_binary_paths = [
                    '/usr/bin/google-chrome',
                    '/usr/bin/google-chrome-stable',
                    '/usr/bin/chromium-browser',
                    '/usr/bin/chromium'
                ]
            elif is_windows:
                # Windows Chrome detection
                chrome_binary_paths = [
                    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                    os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Google', 'Chrome', 'Application', 'chrome.exe')
                ]
            else:
                # Linux Chrome paths
                chrome_binary_paths = [
                    '/usr/bin/google-chrome',
                    '/usr/bin/google-chrome-stable',
                    '/usr/bin/chromium-browser',
                    '/usr/bin/chromium'
                ]
            
            for chrome_path in chrome_binary_paths:
                if os.path.exists(chrome_path):
                    chrome_options.binary_location = chrome_path
                    self.logger.info(f"Using Chrome binary: {chrome_path}")
                    break
            
            # Try to create the driver with multiple fallback approaches
            # Method 1: Try with WebDriverManager (auto-download) - Works best on Windows
            if not driver_created:
                try:
                    self.logger.info("Trying with ChromeDriverManager (auto-download)...")
                    from selenium.webdriver.chrome.service import Service
                    from webdriver_manager.chrome import ChromeDriverManager
                    
                    # Set cache directory based on OS
                    if is_docker:
                        cache_dir = os.path.join('/app', '.wdm')
                    elif is_windows:
                        cache_dir = os.path.join(os.path.expanduser('~'), '.wdm')
                    else:
                        cache_dir = os.path.join(os.path.expanduser('~'), '.wdm')
                    
                    os.makedirs(cache_dir, exist_ok=True)
                    
                    # Set WDM environment variables for latest version
                    os.environ['WDM_LOCAL'] = '1'
                    os.environ['WDM_LOG_LEVEL'] = '0'
                    os.environ['WDM_CACHE_DIR'] = cache_dir
                    
                    # Use the latest WebDriverManager API (v5+)
                    driver_manager = ChromeDriverManager()
                    driver_path = driver_manager.install()
                    service = Service(driver_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    driver_created = True
                    self.logger.info("Chrome driver initialized with WebDriverManager")
                    
                except Exception as e:
                    self.logger.warning(f"WebDriverManager failed: {e}")
            
            if not driver_created:
                raise Exception("All Chrome driver initialization methods failed")
            
            # Method 2: Try with system chromedriver (mainly for Linux/Docker)
            if not driver_created and (not is_windows or is_docker):
                try:
                    from selenium.webdriver.chrome.service import Service
                    
                    chromedriver_paths = [
                        '/usr/bin/chromedriver',
                        '/usr/local/bin/chromedriver',
                        '/opt/chromedriver/chromedriver'
                    ]
                    
                    for driver_path in chromedriver_paths:
                        if os.path.exists(driver_path):
                            service = Service(driver_path)
                            self.driver = webdriver.Chrome(service=service, options=chrome_options)
                            driver_created = True
                            self.logger.info(f"Chrome driver initialized with: {driver_path}")
                            break
                    
                    if not driver_created:
                        # Fallback: Try without explicit service
                        self.driver = webdriver.Chrome(options=chrome_options)
                        driver_created = True
                        self.logger.info("Chrome driver initialized with default service")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to initialize with system driver: {e}")
            
            if not driver_created:
                raise Exception("All Chrome driver initialization methods failed")
            
            # Configure driver to avoid detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.logger.info("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Selenium: {e}")
            self.logger.warning("Selenium not available. Will use requests+BeautifulSoup only.")
            
            # Check if it's a permission error and disable Selenium permanently
            if "Permission denied" in str(e) or "PermissionError" in str(e):
                self.logger.warning("Permission error detected, disabling Selenium for this session")
                self.use_selenium = False
            
            raise
    
    def scrape_jobs(self, url: str) -> List[JobPosting]:
        """Scrape jobs from the given URL using ONLY Selenium."""
        jobs = []
        
        # SELENIUM-ONLY MODE: No fallback to requests+BeautifulSoup
        self.logger.info("SELENIUM-ONLY MODE: Using ONLY Selenium for scraping")
        
        try:
            if not self.driver:
                self.setup_selenium()
            jobs = self._scrape_with_selenium(url)
            if jobs:
                self.logger.info(f"Successfully scraped {len(jobs)} jobs with Selenium")
                return jobs
            else:
                self.logger.info("No jobs found with Selenium - this is normal for some pages")
                return []
        except Exception as e:
            self.logger.error(f"Selenium scraping failed: {e}")
            # No fallback - raise error to force Selenium troubleshooting
            raise Exception(f"SELENIUM-ONLY MODE: Selenium failed and no fallback available: {e}")
    
    def _scrape_with_requests(self, url: str) -> List[JobPosting]:
        """DISABLED: Requests method removed in SELENIUM-ONLY mode."""
        self.logger.error("❌ SELENIUM-ONLY MODE: Requests+BeautifulSoup method disabled")
        raise Exception("❌ SELENIUM-ONLY MODE: Requests+BeautifulSoup method disabled")
    
    def _scrape_with_selenium(self, url: str) -> List[JobPosting]:
        """Scrape jobs using Selenium for JavaScript-rendered content."""
        try:
            # Ensure driver is available and valid
            if not self.driver:
                self.setup_selenium()
            
            # Test if driver session is still valid
            try:
                self.driver.current_url  # This will throw if session is invalid
            except Exception:
                self.logger.warning("Selenium session invalid, reinitializing...")
                self.cleanup()  # Clean up old driver
                self.setup_selenium()  # Create new driver
            
            self.logger.info(f"SELENIUM-ONLY: Navigating to {url}")
            self.driver.get(url)
            
            # Wait for job listings to load
            wait = WebDriverWait(self.driver, 30)  # Increased timeout
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Give extra time for dynamic content to load
            self.logger.info("SELENIUM-ONLY: Waiting for dynamic content to load...")
            time.sleep(5)
            
            # Additional wait to ensure all content is loaded
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            return self._parse_job_listings(soup, url)
            
        except Exception as e:
            self.logger.error(f"SELENIUM-ONLY: Failed to scrape with Selenium: {e}")
            raise
    
    def _parse_with_alternative_methods(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """Alternative parsing methods when primary parsing fails."""
        jobs = []
        
        try:
            # Method 1: Look for any links that might be job-related
            self.logger.info("Trying alternative method 1: Link-based parsing")
            all_links = soup.find_all('a', href=True)
            
            job_keywords = ['job', 'position', 'role', 'career', 'opportunity', 'apply', 'hire', 'work']
            potential_jobs = []
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Check if link or text contains job-related keywords
                if (text and len(text) > 3 and len(text) < 200 and
                    any(keyword in href.lower() for keyword in job_keywords) or
                    any(keyword in text.lower() for keyword in job_keywords)):
                    
                    # Build full URL
                    if href.startswith('/'):
                        full_url = base_url.rstrip('/') + href
                    elif href.startswith(('http://', 'https://')):
                        full_url = href
                    else:
                        continue
                    
                    # Generate basic job posting
                    job_id = hashlib.md5(full_url.encode()).hexdigest()[:12]
                    
                    job = JobPosting(
                        job_id=job_id,
                        title=text,
                        url=full_url,
                        location="Location TBD",
                        posted_date=datetime.now().strftime("%Y-%m-%d"),
                        description=f"Potential job opportunity: {text}"
                    )
                    potential_jobs.append(job)
            
            # Filter and limit results
            filtered_jobs = []
            seen_urls = set()
            
            for job in potential_jobs[:20]:  # Limit to first 20 potential jobs
                if (job.url not in seen_urls and 
                    'amazon' in job.url.lower() and
                    len(job.title) > 5):
                    seen_urls.add(job.url)
                    filtered_jobs.append(job)
            
            self.logger.info(f"Alternative method 1 found {len(filtered_jobs)} potential jobs")
            jobs.extend(filtered_jobs[:5])  # Take top 5
            
            # Method 2: Look for structured data or JSON-LD
            self.logger.info("Trying alternative method 2: Structured data parsing")
            script_tags = soup.find_all('script', type='application/ld+json')
            
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                        job_id = hashlib.md5(str(data).encode()).hexdigest()[:12]
                        
                        job = JobPosting(
                            job_id=job_id,
                            title=data.get('title', 'Job Title TBD'),
                            url=data.get('url', base_url),
                            location=str(data.get('jobLocation', {}).get('address', 'Location TBD')),
                            posted_date=data.get('datePosted', datetime.now().strftime("%Y-%m-%d")),
                            description=data.get('description', '')[:500]  # Limit description
                        )
                        jobs.append(job)
                        
                except (json.JSONDecodeError, KeyError):
                    continue
            
            self.logger.info(f"Alternative methods found total {len(jobs)} jobs")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Alternative parsing methods failed: {e}")
            return []
    
    def _parse_amazon_specific(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """Amazon-specific parsing for when standard methods fail."""
        jobs = []
        
        try:
            self.logger.info("Trying Amazon-specific content extraction")
            
            # Method 1: Look for any href that contains amazon job patterns
            page_content = str(soup)
            
            # Extract potential job URLs from the page content
            import re
            
            # Look for Amazon job URLs in the HTML
            job_url_patterns = [
                r'https://hiring\.amazon\.[^"\s]+',
                r'https://[^"\s]*amazon[^"\s]*job[^"\s]*',
                r'https://[^"\s]*job[^"\s]*amazon[^"\s]*',
                r'/job[^"\s]*',
                r'/position[^"\s]*',
                r'/apply[^"\s]*'
            ]
            
            found_urls = set()
            for pattern in job_url_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                for match in matches:
                    if match.startswith('/'):
                        full_url = base_url.rstrip('/') + match
                    else:
                        full_url = match
                    
                    # Basic validation
                    if len(full_url) > 20 and ('job' in full_url.lower() or 'position' in full_url.lower()):
                        found_urls.add(full_url.strip('"\'\''))
            
            # Method 2: Look for job-related text patterns
            text_content = soup.get_text()
            job_keywords = ['warehouse', 'driver', 'associate', 'operator', 'fulfillment', 'delivery', 'logistics']
            location_keywords = ['toronto', 'vancouver', 'montreal', 'calgary', 'ottawa', 'canada']
            
            lines = text_content.split('\n')
            potential_job_titles = []
            
            for line in lines:
                line = line.strip()
                if (len(line) > 10 and len(line) < 100 and 
                    any(keyword in line.lower() for keyword in job_keywords) and
                    any(keyword in line.lower() for keyword in location_keywords)):
                    potential_job_titles.append(line)
            
            # Create job postings from found URLs
            for i, url in enumerate(list(found_urls)[:5]):  # Limit to 5
                job_id = hashlib.md5(url.encode()).hexdigest()[:12]
                
                # Try to get a meaningful title
                title = f"Amazon Job Opportunity {i+1}"
                if i < len(potential_job_titles):
                    title = potential_job_titles[i][:50]  # Truncate long titles
                
                job = JobPosting(
                    job_id=job_id,
                    title=title,
                    url=url,
                    location="Canada",
                    posted_date=datetime.now().strftime("%Y-%m-%d"),
                    description=f"Amazon job opportunity found via enhanced parsing: {title}"
                )
                jobs.append(job)
            
            # Method 3: Strict mode - no fake data generation
            if not jobs:
                self.logger.info("No real job postings found - maintaining data integrity")
                # Return empty list to maintain data integrity
                return []
            
            self.logger.info(f"Amazon-specific parsing found {len(jobs)} job opportunities")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Amazon-specific parsing failed: {e}")
            return []
    
    def _parse_job_listings(self, soup: BeautifulSoup, base_url: str) -> List[JobPosting]:
        """Parse job listings from BeautifulSoup object with improved error handling."""
        jobs = []
        
        try:
            # Only extract real job postings - no fake data generation
            if "amazon" in base_url.lower():
                real_jobs = self._extract_real_amazon_jobs(soup, base_url)
                if real_jobs:
                    self.logger.info(f"Found {len(real_jobs)} real job postings")
                    return real_jobs
                else:
                    self.logger.info("No real job postings found on Amazon page with primary method")
                    return []
            else:
                # Use generic job parsing for non-Amazon sites
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
                
                # More flexible criteria: Accept URLs that are likely job applications
                if (any(pattern in href.lower() for pattern in ['/job', '/position', '/apply', '/application', 'careers']) and 
                    ('amazon' in href.lower() or 'amazon' in base_url.lower()) and
                    text and len(text) > 3):
                    
                    if href.startswith('/'):
                        full_url = base_url.rstrip('/') + href
                    else:
                        full_url = href
                    
                    # More flexible job title validation
                    if (len(text) > 3 and 
                        not any(skip in text.lower() for skip in ['home', 'about', 'contact', 'help', 'support', 'privacy', 'terms'])):
                        real_job_urls.add((full_url, text))
            
            # Process real job URLs with more flexible validation
            for url, title in real_job_urls:
                # More flexible validation: URL should contain job-related patterns
                if ('amazon' in url.lower() or 'amazon' in base_url.lower()):
                    
                    import hashlib
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
                job = self._extract_job_info_generic(element, base_url)
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

class JobMonitor:
    """Main job monitoring class that manages scraping and job storage."""
    
    def __init__(self):
        # Initialize logger first before any other operations
        self.logger = logging.getLogger('monitor')
        
        self.config = self.load_config()
        self.setup_logging()
        
        # FORCE SELENIUM USAGE - Always initialize with Selenium
        self.scraper = JobScraper(use_selenium=True)  # ALWAYS TRUE
        
        # MANDATORY Selenium setup - no fallback allowed
        try:
            self.scraper.setup_selenium()
            self.logger.info("✅ Selenium initialized successfully - SELENIUM-ONLY MODE")
        except Exception as e:
            self.logger.error(f"❌ CRITICAL: Selenium setup failed in SELENIUM-ONLY mode: {e}")
            # In selenium-only mode, we must raise error instead of continuing
            raise RuntimeError(f"SELENIUM-ONLY MODE: Cannot continue without Selenium: {e}")
        
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
            os.getenv('AMAZON_URLS', 'https://hiring.amazon.ca/app#/jobsearch').split(',')[0]
        ]
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '30'))
        
        # Add caching for frequent API calls
        self._status_cache = None
        self._status_cache_time = 0
        self._jobs_cache = None
        self._jobs_cache_time = 0
        self._cache_ttl = 5  # Cache for 5 seconds to reduce load
        
        # Load existing jobs from file
        self._load_jobs()
        
        # Setup logging handler to capture logs
        self._setup_log_handler()
    def load_config(self) -> Dict:
        """Load configuration from environment variables with production defaults."""
        return {
            'use_selenium': True,  # FORCED TRUE in SELENIUM-ONLY mode
            'poll_interval': int(os.getenv('POLL_INTERVAL', '30')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO').upper(),
            'auto_start': os.getenv('AUTO_START_MONITORING', 'true').lower() == 'true'
        }
    
    def setup_logging(self):
        """Setup logging for production environment."""
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Production logging configuration
        logging.basicConfig(
            level=getattr(logging, self.config.get('log_level', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/api_bot.log'),
                logging.StreamHandler()
            ]
        )
        
        # Reduce noise from third-party libraries
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
    
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
        """Save jobs to JSON file and invalidate cache."""
        try:
            with open('jobs.json', 'w') as f:
                jobs_data = [asdict(job) for job in self.jobs.values()]
                json.dump(jobs_data, f, indent=2, default=str)
            
            # Invalidate caches when jobs are updated
            self._jobs_cache = None
            self._status_cache = None
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
                
                if jobs:
                    self.logger.info(f"Found {len(jobs)} real job postings from {url}")
                else:
                    self.logger.info(f"No real job postings found at {url}. Fake data generation has been disabled.")
                
                for job in jobs:
                    if job.job_id not in self.jobs:
                        self.jobs[job.job_id] = job
                        new_jobs_count += 1
                        self.stats['new_jobs_this_session'] += 1
                        self.add_log('SUCCESS', f'New REAL job found: {job.title} - {job.location} - {job.url}')
                        
                        # Open in browser if configured
                        if os.getenv('AUTO_OPEN_BROWSER', 'false').lower() == 'true':
                            webbrowser.open(job.url)
                
                self.stats['total_jobs_found'] = len(self.jobs)
                
            except Exception as e:
                self.logger.error(f"Error checking {url}: {e}")
                self.stats['errors'] += 1
        
        if new_jobs_count > 0:
            self._save_jobs()
            self.add_log('INFO', f'Check completed. Found {new_jobs_count} new REAL jobs.')
        else:
            self.add_log('INFO', '✅ Check completed. No fake data generated - only real job postings are returned.')
    
    def get_jobs(self, limit: int = 50) -> List[Dict]:
        """Get list of jobs with caching."""
        now = time.time()
        
        # Return cached jobs if still valid
        if self._jobs_cache and (now - self._jobs_cache_time) < self._cache_ttl:
            return self._jobs_cache[:limit]
        
        jobs_list = list(self.jobs.values())
        # Sort by detected_at descending (newest first)
        jobs_list.sort(key=lambda x: x.detected_at, reverse=True)
        
        # Cache the jobs
        self._jobs_cache = [asdict(job) for job in jobs_list]
        self._jobs_cache_time = now
        
        return self._jobs_cache[:limit]
    
    def get_status(self) -> Dict:
        """Get current monitoring status with caching."""
        now = time.time()
        
        # Return cached status if still valid
        if self._status_cache and (now - self._status_cache_time) < self._cache_ttl:
            return self._status_cache
        
        # In SELENIUM-ONLY mode, always show Selenium as enabled
        selenium_status = "On"
        selenium_driver_status = "Ready" if self.scraper.driver else "Initializing"
        
        status = {
            'is_running': self.is_running,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'total_jobs': len(self.jobs),
            'stats': self.stats,
            'config': {
                'poll_interval': self.poll_interval,
                'target_urls': self.target_urls,
                'use_selenium': True,  # ALWAYS TRUE in this version
                'selenium_status': selenium_status,
                'selenium_driver_status': selenium_driver_status
            }
        }
        
        # Cache the status
        self._status_cache = status
        self._status_cache_time = now
        
        return status
    
    def get_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent logs."""
        return list(self.logs)[-limit:]
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_monitoring()
        self.scraper.cleanup()

# Initialize the job monitor with error handling
try:
    job_monitor = JobMonitor()
except Exception as e:
    # Create a minimal logger for error reporting
    import logging
    logger = logging.getLogger('startup')
    logger.error(f"Failed to initialize JobMonitor: {e}")
    
    # Create a fallback JobMonitor with minimal functionality
    class FallbackJobMonitor:
        def __init__(self):
            self.logger = logging.getLogger('fallback')
            self.jobs = {}
            self.logs = []
            self.is_running = False
            self.stats = {'total_checks': 0, 'total_jobs_found': 0, 'new_jobs_this_session': 0, 'errors': 1}
            self.logger.warning("Running in fallback mode due to initialization error")
        
        def get_jobs(self, limit=50): return []
        def get_status(self): return {'is_running': False, 'error': 'Initialization failed'}
        def get_logs(self, limit=50): return [{'timestamp': datetime.now().isoformat(), 'level': 'ERROR', 'message': 'JobMonitor failed to initialize'}]
        async def start_monitoring(self): return
        def stop_monitoring(self): return
        def cleanup(self): return
        def _save_jobs(self): return
    
    job_monitor = FallbackJobMonitor()

# Rate limiting to prevent excessive API calls
class RateLimiter:
    def __init__(self):
        self.clients = defaultdict(lambda: {"requests": 0, "last_reset": time.time()})
        self.lock = Lock()
        self.requests_per_minute = 60  # Allow 60 requests per minute per IP
        self.window_size = 60  # 1 minute window
    
    def is_allowed(self, client_ip: str) -> bool:
        with self.lock:
            now = time.time()
            client_data = self.clients[client_ip]
            
            # Reset counter if window has passed
            if now - client_data["last_reset"] >= self.window_size:
                client_data["requests"] = 0
                client_data["last_reset"] = now
            
            # Check if within limits
            if client_data["requests"] < self.requests_per_minute:
                client_data["requests"] += 1
                return True
            return False

# Initialize rate limiter
rate_limiter = RateLimiter()

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

# CORS middleware with rate limiting considerations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    
    # Skip rate limiting for health checks from known cloud platforms
    if any(path in request.url.path for path in ["/health", "/"]) and "health" in request.headers.get("user-agent", "").lower():
        response = await call_next(request)
        return response
    
    # Apply rate limiting to API endpoints
    if request.url.path in ["/status", "/jobs", "/logs"]:
        if not rate_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down your polling rate."}
            )
    
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
    return response

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

@app.get("/health")
async def health_check():
    """Lightweight health check for cloud platforms."""
    return {"status": "healthy", "service": "amazon-job-monitor"}

@app.get("/jobs")
async def get_jobs(limit: int = 50):
    """Get list of detected jobs."""
    try:
        jobs = job_monitor.get_jobs(limit)
        response = JSONResponse({"jobs": jobs, "total": len(job_monitor.jobs)})
        response.headers["Cache-Control"] = "public, max-age=5"
        response.headers["X-Recommended-Poll-Interval"] = "60"  # Suggest 60 second polling for jobs
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get current monitoring status."""
    try:
        status = job_monitor.get_status()
        response = JSONResponse(status)
        response.headers["Cache-Control"] = "public, max-age=5"
        response.headers["X-Recommended-Poll-Interval"] = "30"  # Suggest 30 second polling
        return response
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
        response = JSONResponse({"logs": logs})
        response.headers["Cache-Control"] = "public, max-age=10"
        response.headers["X-Recommended-Poll-Interval"] = "30"  # Suggest 30 second polling for logs
        return response
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
            # In SELENIUM-ONLY mode, always keep Selenium enabled
            if not request.use_selenium:
                return {"message": "SELENIUM-ONLY MODE: Cannot disable Selenium", "status": "warning"}
            # Selenium already enabled, no change needed
        
        return {"message": "Configuration updated", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/logs")
async def clear_logs():
    """Clear all log messages."""
    try:
        job_monitor.logs.clear()
        return {"message": "All logs cleared", "status": "success"}
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

@app.delete("/jobs/fake")
async def clear_fake_jobs():
    """Clear fake jobs while keeping real ones."""
    try:
        fake_job_indicators = [
            "Amazon Warehouse Associate - Multiple Locations",
            "Various Locations, Canada",
            "Real Amazon job posting:",
            "Amazon is hiring warehouse associates across Canada"
        ]
        
        original_count = len(job_monitor.jobs)
        fake_jobs_removed = 0
        
        # Filter out fake jobs
        real_jobs = {}
        for job_id, job in job_monitor.jobs.items():
            is_fake = any(indicator in job.title or 
                         indicator in job.description or 
                         indicator in job.location 
                         for indicator in fake_job_indicators)
            
            if not is_fake:
                real_jobs[job_id] = job
            else:
                fake_jobs_removed += 1
        
        job_monitor.jobs = real_jobs
        job_monitor._save_jobs()
        job_monitor.stats['total_jobs_found'] = len(real_jobs)
        
        return {
            "message": f"Removed {fake_jobs_removed} fake jobs. {len(real_jobs)} real jobs retained.",
            "status": "success",
            "removed": fake_jobs_removed,
            "remaining": len(real_jobs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Get port from environment
    port = int(os.getenv('API_PORT', '8000'))
    host = os.getenv('API_HOST', '0.0.0.0')
    
    job_monitor.logger.info(f"🚀 SELENIUM-ONLY MODE: Starting API server on {host}:{port}")
    
    # Auto-start monitoring after server starts
    if os.getenv('AUTO_START_MONITORING', 'true').lower() == 'true':
        import threading
        import time
        
        def delayed_start():
            time.sleep(2)  # Wait for server to start
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(job_monitor.start_monitoring())
            job_monitor.logger.info("Auto-started job monitoring")
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=delayed_start, daemon=True)
        monitor_thread.start()
    
    # Run the API server
    uvicorn.run(
        "api_bot:app", 
        host=host, 
        port=port,
        reload=False,  # Disable reload in production
        access_log=True,
        log_level="info"
    )