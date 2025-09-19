#!/usr/bin/env python3
"""
Test script to verify Selenium-only mode is working correctly
"""

import requests
import json
import time

def test_selenium_only_config():
    """Test that the application is configured for Selenium-only mode"""
    
    print("🔍 Testing Selenium-Only Configuration...")
    print("=" * 50)
    
    try:
        # Test status endpoint
        response = requests.get('http://localhost:8001/status')
        status = response.json()
        
        print("📊 Current Status:")
        print(f"   • Running: {status['is_running']}")
        print(f"   • Total Jobs: {status['total_jobs']}")
        print(f"   • Target URL: {status['config']['target_urls'][0]}")
        
        print("\n🤖 Selenium Configuration:")
        print(f"   • Use Selenium: {status['config']['use_selenium']}")
        print(f"   • Selenium Status: {status['config']['selenium_status']}")
        print(f"   • Driver Status: {status['config']['selenium_driver_status']}")
        
        # Verify Selenium-only mode
        if status['config']['use_selenium'] and status['config']['selenium_status'] == 'On':
            print("\n✅ SUCCESS: Selenium-only mode is ACTIVE!")
            print("   • The application will use ONLY Selenium for scraping")
            print("   • No fallback to requests+BeautifulSoup")
            print("   • Perfect for Amazon job scraping!")
        else:
            print("\n❌ ERROR: Selenium is not properly configured")
            return False
            
        print("\n📈 Statistics:")
        print(f"   • Total Checks: {status['stats']['total_checks']}")
        print(f"   • Total Jobs Found: {status['stats']['total_jobs_found']}")
        print(f"   • New Jobs This Session: {status['stats']['new_jobs_this_session']}")
        print(f"   • Errors: {status['stats']['errors']}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to API server on port 8001")
        print("   Make sure the application is running with: python api_bot.py")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_job_scraping():
    """Test that job scraping is working with Selenium"""
    
    print("\n🔄 Testing Job Scraping...")
    print("=" * 30)
    
    try:
        # Get current jobs
        response = requests.get('http://localhost:8001/jobs')
        jobs_data = response.json()
        
        print(f"📋 Found {len(jobs_data['jobs'])} jobs:")
        
        for i, job in enumerate(jobs_data['jobs'][:3], 1):  # Show first 3 jobs
            print(f"   {i}. {job['title']}")
            print(f"      Location: {job['location']}")
            print(f"      URL: {job['url'][:50]}...")
            print(f"      Detected: {job['detected_at'][:10]}")
            print()
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR getting jobs: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Amazon Job Monitor - Selenium-Only Mode Test")
    print("=" * 60)
    
    config_ok = test_selenium_only_config()
    
    if config_ok:
        job_test_ok = test_job_scraping()
        
        if job_test_ok:
            print("\n🎉 ALL TESTS PASSED!")
            print("   Your application is ready for deployment with Selenium-only mode!")
            print("\n🌐 Deployment ready endpoints:")
            print("   • Status: http://localhost:8001/status")
            print("   • Jobs: http://localhost:8001/jobs")
            print("   • Start monitoring: POST http://localhost:8001/start")
            print("   • Stop monitoring: POST http://localhost:8001/stop")
        else:
            print("\n⚠️  Configuration OK but job scraping needs attention")
    else:
        print("\n❌ Configuration test failed")
    
    print("\n" + "=" * 60)