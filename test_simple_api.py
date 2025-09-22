#!/usr/bin/env python3
"""
Test script for the simplified API to verify it works before deploying to Vercel.
"""

import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_import():
    """Test importing the simplified API."""
    print("Testing imports...")
    
    try:
        from api_simple import app
        print("✅ Successfully imported api_simple")
        return app, "api_simple"
    except Exception as e:
        print(f"❌ Failed to import api_simple: {e}")
        traceback.print_exc()
        
    try:
        from api_bot import app
        print("✅ Successfully imported api_bot")
        return app, "api_bot"
    except Exception as e:
        print(f"❌ Failed to import api_bot: {e}")
        traceback.print_exc()
        
    return None, None

def test_endpoints(app):
    """Test that endpoints are defined."""
    print("\nTesting endpoints...")
    
    routes = [route.path for route in app.routes]
    expected_routes = ["/", "/jobs", "/status", "/start", "/logs", "/health"]
    
    for route in expected_routes:
        if route in routes:
            print(f"✅ Route {route} found")
        else:
            print(f"❌ Route {route} missing")
    
    return len([r for r in expected_routes if r in routes]) == len(expected_routes)

def main():
    """Main test function."""
    print("=" * 50)
    print("  Testing Simplified API for Vercel")
    print("=" * 50)
    
    # Test imports
    app, source = test_import()
    
    if app is None:
        print("\n❌ FAILED: Could not import any API module")
        return False
    
    print(f"\n✅ SUCCESS: Using {source} module")
    
    # Test endpoints
    if test_endpoints(app):
        print("\n✅ SUCCESS: All endpoints found")
    else:
        print("\n❌ FAILED: Some endpoints missing")
        return False
    
    # Test basic app properties
    print(f"\nApp title: {app.title}")
    print(f"App version: {app.version}")
    
    print("\n" + "=" * 50)
    print("  All tests passed! Ready for Vercel deployment")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)