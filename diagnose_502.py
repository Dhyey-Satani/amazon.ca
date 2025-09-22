#!/usr/bin/env python3
"""
Enhanced 502 Error Diagnostic Tool for Railway Deployment
Analyzes the complete request flow: Railway -> Nginx -> API
"""
import os
import sys
import time
import requests
import subprocess
import socket
from datetime import datetime

def log_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def check_port_binding(port, host="127.0.0.1"):
    """Check if a port is bound and listening"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"⚠️  Error checking port {port}: {e}")
        return False

def check_process_running(process_name):
    """Check if a process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', process_name], 
                               capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def test_api_direct(port):
    """Test API directly without nginx proxy"""
    try:
        response = requests.get(f'http://127.0.0.1:{port}/status', timeout=10)
        return response.status_code, response.json()
    except Exception as e:
        return None, str(e)

def test_nginx_proxy(external_port, api_path="/api/status"):
    """Test nginx proxy to API"""
    try:
        response = requests.get(f'http://127.0.0.1:{external_port}{api_path}', timeout=10)
        return response.status_code, response.text[:200]
    except Exception as e:
        return None, str(e)

def analyze_supervisor_status():
    """Get supervisor process status"""
    try:
        result = subprocess.run(['supervisorctl', 'status'], 
                               capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error getting supervisor status: {e}"

def main():
    print(f"🔍 [{log_timestamp()}] Railway 502 Diagnostic Tool Starting...")
    print("=" * 60)
    
    # Get environment variables
    external_port = int(os.getenv('PORT', '8080'))
    api_port = 8081  # Internal API port
    
    print(f"📊 Configuration Analysis:")
    print(f"   External PORT (Railway -> Nginx): {external_port}")
    print(f"   Internal API PORT (Nginx -> API): {api_port}")
    print()
    
    # Check 1: Process Status
    print(f"🔄 [{log_timestamp()}] Checking Process Status...")
    nginx_running = check_process_running('nginx')
    api_running = check_process_running('api_bot.py')
    
    print(f"   Nginx Process: {'✅ Running' if nginx_running else '❌ Not Running'}")
    print(f"   API Process:   {'✅ Running' if api_running else '❌ Not Running'}")
    
    if not nginx_running or not api_running:
        print(f"\n🆘 CRITICAL: Missing processes detected!")
        print(f"   Supervisor Status:")
        print(f"   {analyze_supervisor_status()}")
        return 1
    
    # Check 2: Port Binding
    print(f"\n🔌 [{log_timestamp()}] Checking Port Binding...")
    nginx_bound = check_port_binding(external_port, "0.0.0.0")
    api_bound = check_port_binding(api_port)
    
    print(f"   Port {external_port} (Nginx):  {'✅ Bound' if nginx_bound else '❌ Not Bound'}")
    print(f"   Port {api_port} (API):     {'✅ Bound' if api_bound else '❌ Not Bound'}")
    
    if not api_bound:
        print(f"\n🆘 CRITICAL: API not bound to port {api_port}!")
        print(f"   This will cause 502 errors - nginx can't reach API")
        return 1
    
    # Check 3: API Direct Test
    print(f"\n🎯 [{log_timestamp()}] Testing API Direct Connection...")
    api_status, api_response = test_api_direct(api_port)
    
    if api_status == 200:
        print(f"   ✅ API Direct: HTTP {api_status} - {api_response}")
    else:
        print(f"   ❌ API Direct: Failed - {api_response}")
        print(f"   🆘 CRITICAL: API not responding on port {api_port}")
        return 1
    
    # Check 4: Nginx Proxy Test
    print(f"\n🔀 [{log_timestamp()}] Testing Nginx Proxy...")
    proxy_status, proxy_response = test_nginx_proxy(external_port)
    
    if proxy_status == 200:
        print(f"   ✅ Nginx Proxy: HTTP {proxy_status}")
        print(f"   📝 Response: {proxy_response[:100]}...")
    else:
        print(f"   ❌ Nginx Proxy: Failed - {proxy_response}")
        print(f"   🆘 502 ERROR SOURCE: Nginx cannot proxy to API")
        
        # Additional diagnostics for 502
        print(f"\n🔍 502 Error Analysis:")
        print(f"   1. API is running: ✅")
        print(f"   2. API port {api_port} is bound: ✅")
        print(f"   3. API responds directly: ✅")
        print(f"   4. Nginx proxy fails: ❌")
        print(f"   ")
        print(f"   🔧 Likely causes:")
        print(f"   - Nginx config has wrong API port")
        print(f"   - API_PORT_PLACEHOLDER not replaced")
        print(f"   - Nginx restarted but API port changed")
        
        return 1
    
    # All checks passed
    print(f"\n✅ [{log_timestamp()}] All Diagnostics PASSED!")
    print(f"   🎉 No 502 error detected - system is healthy")
    print(f"   🌐 Railway URL should work correctly")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)