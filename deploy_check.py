#!/usr/bin/env python3
"""
Deployment Readiness Checker for Amazon Job Monitor
Validates that the project is ready for different deployment environments
"""

import os
import platform
import json
from pathlib import Path

def check_local_deployment():
    """Check if project is ready for local deployment"""
    print("🖥️  LOCAL DEPLOYMENT CHECK")
    print("-" * 50)
    
    checks = {
        "Python Environment": check_python(),
        "Required Files": check_required_files(),
        "Dependencies": check_dependencies(),
        "Environment Config": check_env_config(),
        "Chrome Available": check_chrome_local(),
    }
    
    all_passed = all(checks.values())
    
    for check, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check}")
    
    print(f"\n🎯 Local Deployment: {'READY' if all_passed else 'NEEDS FIXES'}")
    return all_passed

def check_cloud_deployment():
    """Check if project is ready for cloud deployment"""
    print("\n☁️  CLOUD DEPLOYMENT CHECK")
    print("-" * 50)
    
    checks = {
        "Dockerfile Present": os.path.exists("Dockerfile"),
        "Requirements File": os.path.exists("requirements.txt"),
        "Production Config": os.path.exists(".env.production"),
        "API Entry Point": check_api_entry(),
        "Cross-Platform Code": check_cross_platform(),
        "No Hardcoded Paths": check_no_hardcoded_paths(),
    }
    
    all_passed = all(checks.values())
    
    for check, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check}")
    
    print(f"\n🎯 Cloud Deployment: {'READY' if all_passed else 'NEEDS FIXES'}")
    return all_passed

def check_python():
    """Check Python version"""
    import sys
    version = sys.version_info
    return version.major == 3 and version.minor >= 8

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        "api_bot.py",
        "requirements.txt",
        "README.md",
        ".env"
    ]
    return all(os.path.exists(f) for f in required_files)

def check_dependencies():
    """Check if key dependencies are available"""
    try:
        import requests
        import selenium
        import fastapi
        import uvicorn
        from bs4 import BeautifulSoup  # beautifulsoup4 imports as bs4
        return True
    except ImportError as e:
        print(f"   Missing dependency: {e}")
        return False

def check_env_config():
    """Check environment configuration"""
    return os.path.exists(".env") and os.path.getsize(".env") > 0

def check_chrome_local():
    """Check if Chrome is available locally"""
    if platform.system() == "Windows":
        chrome_paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
        ]
        return any(os.path.exists(path) for path in chrome_paths)
    else:
        chrome_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium-browser'
        ]
        return any(os.path.exists(path) for path in chrome_paths)

def check_api_entry():
    """Check if API has proper entry point"""
    try:
        with open("api_bot.py", "r") as f:
            content = f.read()
            return 'if __name__ == "__main__":' in content and "uvicorn.run" in content
    except:
        return False

def check_cross_platform():
    """Check if code handles cross-platform scenarios"""
    try:
        with open("api_bot.py", "r") as f:
            content = f.read()
            return "platform.system()" in content and "is_docker" in content
    except:
        return False

def check_no_hardcoded_paths():
    """Check for problematic hardcoded paths that might break deployment"""
    try:
        with open("api_bot.py", "r") as f:
            content = f.read()
            # Check for hardcoded user-specific paths (not Chrome installation paths)
            bad_patterns = [
                "/Users/HP/",  # User-specific path
                "C:\\Users\\HP",  # User-specific path
                "c:\\users\\hp"   # User-specific path
            ]
            return not any(pattern.lower() in content.lower() for pattern in bad_patterns)
    except:
        return False

def generate_deployment_summary():
    """Generate deployment readiness summary"""
    print("\n" + "=" * 70)
    print("🚀 DEPLOYMENT READINESS SUMMARY")
    print("=" * 70)
    
    local_ready = check_local_deployment()
    cloud_ready = check_cloud_deployment()
    
    print(f"\n📊 OVERALL STATUS:")
    print(f"   Local Development: {'✅ READY' if local_ready else '⚠️  NEEDS WORK'}")
    print(f"   Cloud Production:  {'✅ READY' if cloud_ready else '⚠️  NEEDS WORK'}")
    
    if local_ready and cloud_ready:
        print(f"\n🎉 PROJECT IS DEPLOYMENT READY!")
        print(f"   ✅ Ready for local Windows development")
        print(f"   ✅ Ready for cloud deployment (Render, Railway, etc.)")
    elif local_ready:
        print(f"\n⚠️  PROJECT IS PARTIALLY READY")
        print(f"   ✅ Local development works")
        print(f"   ⚠️  Cloud deployment needs attention")
    else:
        print(f"\n❌ PROJECT NEEDS FIXES")
        print(f"   ❌ Both local and cloud deployment need work")
    
    print(f"\n📋 NEXT STEPS:")
    if not local_ready:
        print(f"   1. Fix local deployment issues above")
    if not cloud_ready:
        print(f"   2. Address cloud deployment requirements")
    if local_ready and cloud_ready:
        print(f"   1. Test local deployment: python api_bot.py")
        print(f"   2. Deploy to cloud using Dockerfile")
        print(f"   3. Set environment variables from .env.production")
    
    print("=" * 70)

if __name__ == "__main__":
    print("🔍 AMAZON JOB MONITOR - DEPLOYMENT READINESS CHECK")
    print(f"📁 Directory: {os.getcwd()}")
    print(f"🖥️  System: {platform.system()} {platform.release()}")
    
    generate_deployment_summary()