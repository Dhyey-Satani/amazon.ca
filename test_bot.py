#!/usr/bin/env python3
"""
Test script to verify the Amazon Job Bot functionality.
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import requests
        print("✓ requests imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import requests: {e}")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✓ BeautifulSoup imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import BeautifulSoup: {e}")
        return False
    
    try:
        from selenium import webdriver
        print("✓ selenium imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import selenium: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import python-dotenv: {e}")
        return False
        
    try:
        import sqlite3
        print("✓ sqlite3 imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import sqlite3: {e}")
        return False

    try:
        import win10toast
        print("✓ win10toast imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import win10toast: {e}")
        return False
    
    return True

def test_bot_class():
    """Test if the bot class can be instantiated."""
    print("\nTesting bot class instantiation...")
    
    try:
        from bot import AmazonJobBot, DatabaseManager, NotificationManager, AmazonJobScraper
        print("✓ Bot classes imported successfully")
        
        # Test database manager
        db = DatabaseManager("test.db")
        print("✓ DatabaseManager created successfully")
        
        # Test notification manager
        notifications = NotificationManager()
        print("✓ NotificationManager created successfully")
        
        # Test scraper (without Selenium for now)
        scraper = AmazonJobScraper(use_selenium=False)
        print("✓ AmazonJobScraper created successfully")
        
        # Clean up test database
        if os.path.exists("test.db"):
            os.remove("test.db")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to create bot components: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from bot import AmazonJobBot
        
        # Create bot instance (should load config)
        bot = AmazonJobBot()
        print("✓ Configuration loaded successfully")
        print(f"  Poll interval: {bot.config['poll_interval']} seconds")
        print(f"  URLs to monitor: {len(bot.config['urls'])}")
        print(f"  Use Selenium: {bot.config['use_selenium']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False

def main():
    """Main test function."""
    print("Amazon Job Bot - System Test")
    print("=" * 40)
    
    all_tests_passed = True
    
    # Test imports
    if not test_imports():
        all_tests_passed = False
    
    # Test bot classes
    if not test_bot_class():
        all_tests_passed = False
    
    # Test configuration
    if not test_configuration():
        all_tests_passed = False
    
    print("\n" + "=" * 40)
    if all_tests_passed:
        print("🎉 All tests passed! The bot is ready to run.")
        print("\nNext steps:")
        print("1. Edit .env file with your Telegram bot credentials")
        print("2. Run: python bot.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main()