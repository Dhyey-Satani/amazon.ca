#!/usr/bin/env python3
"""
Health check script for Railway deployment debugging
"""
import os
import sys
import requests
import time
import subprocess

def check_environment():
    """Check environment variables and system state"""
    print("=== Environment Check ===")
    print(f"PORT: {os.getenv('PORT', 'Not set')}")
    print(f"USE_SELENIUM: {os.getenv('USE_SELENIUM', 'Not set')}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    print("===========================")

def check_services():
    """Check if services are running"""
    print("=== Service Check ===")
    
    # Check if nginx is running
    try:
        result = subprocess.run(['pgrep', 'nginx'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Nginx is running")
        else:
            print("❌ Nginx is not running")
    except Exception as e:
        print(f"❌ Could not check nginx: {e}")
    
    # Check if python API is running
    try:
        result = subprocess.run(['pgrep', '-f', 'api_bot.py'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ API process is running")
        else:
            print("❌ API process is not running")
    except Exception as e:
        print(f"❌ Could not check API process: {e}")
    
    print("======================")

def check_ports():
    """Check if ports are listening"""
    print("=== Port Check ===")
    
    # Check external port (Railway PORT)
    port = os.getenv('PORT', '8080')
    try:
        response = requests.get(f'http://localhost:{port}/', timeout=5)
        print(f"✅ Port {port} (nginx) is responding: {response.status_code}")
    except Exception as e:
        print(f"❌ Port {port} (nginx) is not responding: {e}")
    
    # Check internal API port
    try:
        response = requests.get('http://localhost:8081/status', timeout=5)
        print(f"✅ Port 8081 (API) is responding: {response.status_code}")
    except Exception as e:
        print(f"❌ Port 8081 (API) is not responding: {e}")
    
    print("===================")

def check_files():
    """Check if required files exist and have correct permissions"""
    print("=== File Check ===")
    
    files_to_check = [
        '/app/api_bot.py',
        '/var/www/html/index.html',
        '/etc/nginx/sites-available/default',
        '/etc/supervisor/conf.d/supervisord.conf'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            print(f"✅ {file_path} exists (size: {stat.st_size} bytes)")
        else:
            print(f"❌ {file_path} does not exist")
    
    print("===================")

if __name__ == "__main__":
    print("🔍 Starting health check...")
    check_environment()
    check_files()
    check_services()
    check_ports()
    print("🔍 Health check complete!")