#!/usr/bin/env python3
"""
Quick test script to verify the backend is working.
Run this to test the backend before opening the dashboard.
"""

import subprocess
import time
import sys
from pathlib import Path

def test_backend():
    """Test if the backend is responding correctly."""
    print("🧪 Testing Backend Connection...")
    
    # Test with curl
    try:
        result = subprocess.run([
            'curl', '-s', '-w', 'Status: %{http_code}\\n', 
            'http://localhost:5001/api/status'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Backend Response:")
            print(result.stdout)
            
            if "200" in result.stdout:
                print("✅ Backend is working correctly!")
                return True
            else:
                print("❌ Backend returned non-200 status")
                return False
        else:
            print("❌ Could not connect to backend")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking Dependencies...")
    
    try:
        import flask
        print(f"✅ Flask {flask.__version__}")
    except ImportError:
        print("❌ Flask not installed")
        return False
    
    try:
        import flask_cors
        print(f"✅ Flask-CORS {flask_cors.__version__}")
    except ImportError:
        print("❌ Flask-CORS not installed")
        return False
    
    return True

def main():
    """Main test function."""
    print("=== Backend Test Script ===")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Missing dependencies. Run: pip install -r requirements.txt")
        return False
    
    print("\n📋 Instructions:")
    print("1. Start the backend in another terminal:")
    print("   cd dashboard/backend/")
    print("   python run.py")
    print("2. Wait for 'Running on http://127.0.0.1:5001' message")
    print("3. Press Enter here to test the connection")
    
    input("\nPress Enter when backend is running...")
    
    # Test the backend
    if test_backend():
        print("\n🎉 Backend test successful!")
        print("You can now open dashboard/index.html in your browser")
        return True
    else:
        print("\n❌ Backend test failed!")
        print("Check that the backend is running on port 5001")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)