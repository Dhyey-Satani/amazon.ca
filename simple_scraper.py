#!/usr/bin/env python3
"""
Simple Amazon Job Scraper - Pay Rate Focus
Runs independently to avoid threading issues
"""

import json
import sys
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_amazon_jobs():
    """Scrape Amazon jobs focusing on Pay rate information."""
    url = "https://hiring.amazon.ca/app#/jobsearch"
    results = {
        "jobs": [],
        "page_messages": [],
        "success": False
    }
    
    playwright = None
    browser = None
    
    try:
        playwright = sync_playwright().start()
        
        # Use Chrome from Downloads
        chrome_path = r"C:\Users\HP\Downloads\chrome-win\chrome.exe"
        
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=chrome_path,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage', 
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        )
        
        context = browser.new_context()
        page = context.new_page()
        
        # Navigate and wait
        page.goto(url, wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(3000)  # Wait 3 seconds
        
        # Get page content
        page_text = page.content()
        soup = BeautifulSoup(page_text, 'html.parser')
        text_content = soup.get_text()
        
        # Check for error messages
        if "Seems like you're visiting the Canada website from the US" in text_content:
            results["page_messages"].append("US visitor redirect detected")
            
        if "We couldn't get your location" in text_content:
            results["page_messages"].append("Location tracking message detected")
            
        if "Sorry, there are no jobs available" in text_content:
            results["page_messages"].append("No jobs available message displayed")
            results["success"] = True
            return results
        
        # Look for job elements
        job_elements = page.query_selector_all('[data-testid*="job"], .job-tile, .job-card')
        
        if not job_elements:
            job_elements = page.query_selector_all('div[role="button"], a[href*="job"]')
        
        results["page_messages"].append(f"Found {len(job_elements)} potential job elements")
        
        # Check for Pay rate
        for i, element in enumerate(job_elements):
            try:
                element_text = element.inner_text() or ""
                
                if "Pay rate" in element_text:
                    # Extract job info
                    job = {
                        "job_id": f"AMZ-PAY-{i}",
                        "title": "Amazon Position with Pay Rate",
                        "url": url,
                        "location": "Canada", 
                        "pay_rate": "Found",
                        "description": element_text[:100] + "...",
                        "detected_at": "2025-09-24T02:00:00"
                    }
                    
                    results["jobs"].append(job)
                    results["page_messages"].append(f"Pay rate job found: {job['title']}")
            
            except Exception as e:
                continue
        
        if not results["jobs"]:
            results["page_messages"].append("No jobs with Pay rate information found")
        
        results["success"] = True
        return results
        
    except Exception as e:
        results["page_messages"].append(f"Scraping error: {str(e)}")
        return results
    finally:
        try:
            if browser:
                browser.close()
            if playwright:
                playwright.stop()
        except:
            pass

if __name__ == "__main__":
    result = scrape_amazon_jobs()
    print(json.dumps(result, indent=2))