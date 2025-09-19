#!/usr/bin/env python3
"""
Test script to verify Selenium setup on Windows
"""

import os
import platform
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('selenium_test')

def test_selenium_setup():
    """Test Selenium setup on Windows."""
    
    print(f"🖥️  System: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {platform.python_version()}")
    print(f"📁 Working Directory: {os.getcwd()}")
    
    # Check if USE_SELENIUM is set
    use_selenium_env = os.getenv('USE_SELENIUM', 'not_set')
    print(f"🔧 USE_SELENIUM environment variable: {use_selenium_env}")
    
    driver = None
    try:
        print("\n🚀 Testing Selenium WebDriver setup...")
        
        # Setup Chrome options for Windows
        chrome_options = Options()
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set user data directory
        user_data_dir = os.path.join(os.path.expanduser('~'), '.chrome_user_data')
        os.makedirs(user_data_dir, exist_ok=True)
        chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        print(f"📂 Chrome user data directory: {user_data_dir}")
        
        # Check for Chrome installation
        chrome_paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Google', 'Chrome', 'Application', 'chrome.exe')
        ]
        
        chrome_found = False
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                chrome_options.binary_location = chrome_path
                print(f"✅ Found Chrome at: {chrome_path}")
                chrome_found = True
                break
        
        if not chrome_found:
            print("⚠️  Chrome not found in standard locations")
        
        # Try to initialize WebDriver using WebDriverManager
        print("\n🔧 Initializing ChromeDriver with WebDriverManager...")
        
        cache_dir = os.path.join(os.path.expanduser('~'), '.wdm')
        os.makedirs(cache_dir, exist_ok=True)
        print(f"📂 WebDriverManager cache directory: {cache_dir}")
        
        # Set environment variable for cache directory
        os.environ['WDM_CACHE_DIR'] = cache_dir
        
        driver_manager = ChromeDriverManager()
        driver_path = driver_manager.install()
        print(f"✅ ChromeDriver installed at: {driver_path}")
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ WebDriver initialized successfully!")
        
        # Test navigation
        print("\n🌐 Testing navigation to Amazon...")
        driver.get("https://hiring.amazon.ca/app#/jobsearch")
        
        print(f"✅ Successfully navigated to: {driver.current_url}")
        print(f"📄 Page title: {driver.title}")
        print(f"📏 Page source length: {len(driver.page_source)} characters")
        
        # Check if page contains job-related content
        page_source = driver.page_source.lower()
        job_indicators = ['job', 'position', 'career', 'apply', 'hiring']
        found_indicators = [indicator for indicator in job_indicators if indicator in page_source]
        
        if found_indicators:
            print(f"✅ Found job-related content: {', '.join(found_indicators)}")
        else:
            print("⚠️  No obvious job-related content found")
        
        print("\n🎉 Selenium test PASSED! Selenium should work with your project.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try: pip install selenium webdriver-manager")
        return False
    except Exception as e:
        print(f"❌ Selenium test FAILED: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("1. Make sure Google Chrome is installed")
        print("2. Check if Windows Defender is blocking the driver")
        print("3. Try running as administrator")
        print("4. Check your internet connection for driver download")
        return False
    finally:
        if driver:
            try:
                driver.quit()
                print("🧹 WebDriver cleaned up")
            except:
                pass

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SELENIUM SETUP TEST FOR WINDOWS")
    print("=" * 60)
    
    success = test_selenium_setup()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST RESULT: SELENIUM IS WORKING!")
        print("✅ Your bot should now use Selenium successfully.")
    else:
        print("❌ TEST RESULT: SELENIUM SETUP FAILED")
        print("❌ The bot will fall back to requests mode.")
    print("=" * 60)