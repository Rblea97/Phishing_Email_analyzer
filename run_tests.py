#!/usr/bin/env python3
"""
Test Runner for AI-Powered Phishing Detection System
Runs the complete test suite with coverage reporting
"""

import sys
import subprocess
import os

def run_tests():
    """Run all tests with coverage reporting"""
    print("🧪 Running AI-Powered Phishing Detection Test Suite...")
    print("=" * 60)
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Run tests with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--cov=services",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ], check=True)
        
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest pytest-cov")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)