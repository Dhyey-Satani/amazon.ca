#!/usr/bin/env python3
"""
Deployment Verification Script for Amazon Job Monitor
Tests all API endpoints after deployment to ensure everything works.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class DeploymentTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        
    def test_endpoint(self, method: str, endpoint: str, expected_status: int = 200, data: Dict = None) -> Dict[str, Any]:
        """Test a single API endpoint."""
        url = f"{self.base_url}{endpoint}"
        print(f"Testing {method} {url}...")
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            success = response.status_code == expected_status
            
            try:
                content = response.json()
            except:
                content = response.text
            
            result = {
                "success": success,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "content": content
            }
            
            if success:
                print(f"✅ SUCCESS: {method} {endpoint}")
            else:
                print(f"❌ FAILED: {method} {endpoint} - Status: {response.status_code}")
                
            return result
            
        except Exception as e:
            print(f"❌ ERROR: {method} {endpoint} - {str(e)}")
            return {"success": False, "error": str(e)}
    
    def run_full_test(self) -> Dict[str, Any]:
        """Run comprehensive deployment test."""
        print(f"🚀 Testing deployment at: {self.base_url}")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Health check
        results['health'] = self.test_endpoint('GET', '/')
        
        # Test 2: Status endpoint
        results['status'] = self.test_endpoint('GET', '/status')
        
        # Test 3: Jobs endpoint
        results['jobs'] = self.test_endpoint('GET', '/jobs')
        
        # Test 4: Logs endpoint
        results['logs'] = self.test_endpoint('GET', '/logs')
        
        # Test 5: Start monitoring
        results['start'] = self.test_endpoint('POST', '/start')
        
        # Wait a moment for monitoring to initialize
        if results['start']['success']:
            print("⏳ Waiting 10 seconds for monitoring to start...")
            time.sleep(10)
            
            # Test 6: Check status after start
            results['status_after_start'] = self.test_endpoint('GET', '/status')
        
        # Test 7: Stop monitoring
        results['stop'] = self.test_endpoint('POST', '/stop')
        
        # Test 8: Check final status
        results['final_status'] = self.test_endpoint('GET', '/status')
        
        # Generate summary
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result.get('success', False))
        
        for test_name, result in results.items():
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n📈 Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Your deployment is working perfectly!")
        elif passed_tests >= total_tests * 0.8:
            print("✅ Most tests passed. Deployment is functional with minor issues.")
        else:
            print("⚠️  Several tests failed. Check deployment configuration.")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests / total_tests,
            "results": results
        }

def main():
    if len(sys.argv) != 2:
        print("Usage: python deployment_test.py <BASE_URL>")
        print("Example: python deployment_test.py https://your-app.koyeb.app")
        sys.exit(1)
    
    base_url = sys.argv[1]
    tester = DeploymentTester(base_url)
    
    try:
        summary = tester.run_full_test()
        
        # Save results to file
        with open('deployment_test_results.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: deployment_test_results.json")
        
        # Exit with appropriate code
        if summary['success_rate'] >= 0.8:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()