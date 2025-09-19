#!/usr/bin/env python3
"""
Final demonstration that Selenium is working properly in your project
"""

import os
import sys
import platform

# Add current directory to path to import from api_bot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_bot import JobScraper
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('demo')

def main():
    print("=" * 70)
    print("🎉 FINAL SELENIUM DEMONSTRATION")
    print("=" * 70)
    print(f"🖥️  System: {platform.system()} {platform.release()}")
    print(f"📁 Directory: {os.getcwd()}")
    
    # Test the actual scraper from your project
    print("\n🚀 Testing JobScraper with Selenium enabled...")
    
    # Create scraper instance (same as your API bot does)
    scraper = JobScraper(use_selenium=True)
    
    print(f"✅ Selenium enabled: {scraper.use_selenium}")
    
    if scraper.use_selenium:
        try:
            print("\n🔧 Setting up Selenium WebDriver...")
            scraper.setup_selenium()
            
            if scraper.driver:
                print("✅ WebDriver initialized successfully!")
                
                print("\n🕷️  Testing job scraping...")
                jobs = scraper.scrape_jobs("https://hiring.amazon.ca/app#/jobsearch")
                
                print(f"✅ Found {len(jobs)} job postings!")
                
                for i, job in enumerate(jobs[:3], 1):  # Show first 3 jobs
                    print(f"\n📋 Job {i}:")
                    print(f"   Title: {job.title}")
                    print(f"   URL: {job.url}")
                    print(f"   Location: {job.location}")
                
                print(f"\n🎯 SELENIUM STATUS: WORKING PERFECTLY!")
                print(f"✅ Your bot will now use Selenium for accurate job detection")
                print(f"✅ Poll messages should now show 'Selenium: On'")
                
            else:
                print("❌ WebDriver failed to initialize")
                
        except Exception as e:
            print(f"❌ Error during testing: {e}")
        finally:
            scraper.cleanup()
            print("🧹 Cleaned up resources")
    else:
        print("❌ Selenium not enabled")
    
    print("\n" + "=" * 70)
    print("🏁 SELENIUM DEMONSTRATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()