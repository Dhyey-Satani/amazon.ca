#!/usr/bin/env python3
"""
Performance monitoring script to analyze API request patterns
and identify high-frequency polling issues
"""

import requests
import time
import json
from collections import defaultdict
from datetime import datetime

def monitor_api_performance(base_url="http://localhost:8000", duration=300):
    """Monitor API performance for specified duration (seconds)."""
    
    print(f"🔍 Monitoring API performance at {base_url} for {duration} seconds...")
    
    start_time = time.time()
    request_counts = defaultdict(int)
    response_times = defaultdict(list)
    errors = []
    
    endpoints = ["/status", "/jobs", "/logs", "/health"]
    
    while time.time() - start_time < duration:
        for endpoint in endpoints:
            try:
                start_req = time.time()
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                end_req = time.time()
                
                request_counts[endpoint] += 1
                response_times[endpoint].append(end_req - start_req)
                
                if response.status_code != 200:
                    errors.append({
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Check for rate limiting headers
                if "X-RateLimit-Limit" in response.headers:
                    print(f"📊 Rate limit info for {endpoint}: {response.headers.get('X-RateLimit-Limit')}")
                
                time.sleep(2)  # Wait 2 seconds between requests
                
            except requests.exceptions.RequestException as e:
                errors.append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        time.sleep(10)  # Wait 10 seconds between full cycles
    
    # Generate report
    print("\n📊 Performance Report:")
    print("=" * 50)
    
    for endpoint in endpoints:
        count = request_counts[endpoint]
        times = response_times[endpoint]
        
        if times:
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            print(f"\n📍 {endpoint}:")
            print(f"   Requests: {count}")
            print(f"   Avg Response Time: {avg_time:.3f}s")
            print(f"   Min Response Time: {min_time:.3f}s")
            print(f"   Max Response Time: {max_time:.3f}s")
    
    if errors:
        print(f"\n❌ Errors encountered: {len(errors)}")
        for error in errors[-5:]:  # Show last 5 errors
            print(f"   {error}")
    
    total_requests = sum(request_counts.values())
    requests_per_minute = (total_requests / duration) * 60
    
    print(f"\n📈 Summary:")
    print(f"   Total Requests: {total_requests}")
    print(f"   Requests per Minute: {requests_per_minute:.1f}")
    print(f"   Duration: {duration}s")

if __name__ == "__main__":
    monitor_api_performance()