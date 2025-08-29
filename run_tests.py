#!/usr/bin/env python3
"""
Test runner script for Phase 2 MVP
Runs comprehensive tests with reporting and validation
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    required_modules = [
        'pytest',
        'services.parser',
        'services.rules'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print("Missing required modules:")
        for module in missing:
            print(f"  - {module}")
        
        if 'pytest' in missing:
            print("\nInstall pytest with: pip install pytest pytest-cov")
        
        return False
    
    return True

def check_fixtures():
    """Check if test fixtures are available"""
    fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
    
    required_fixtures = [
        'safe_newsletter.eml',
        'obvious_phishing.eml',
        'spoofed_display.eml',
        'auth_failure.eml',
        'unicode_spoof.eml'
    ]
    
    missing = []
    for fixture in required_fixtures:
        if not (fixtures_dir / fixture).exists():
            missing.append(fixture)
    
    if missing:
        print("Missing test fixtures:")
        for fixture in missing:
            print(f"  - {fixture}")
        return False
    
    return True

def run_parser_tests():
    """Run parser module tests"""
    print("Running parser tests...")
    cmd = [sys.executable, '-m', 'pytest', 'tests/test_parser.py', '-v']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

def run_rules_tests():
    """Run rule engine tests"""
    print("Running rule engine tests...")
    cmd = [sys.executable, '-m', 'pytest', 'tests/test_rules.py', '-v']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

def run_integration_tests():
    """Run integration tests"""
    print("Running integration tests...")
    cmd = [sys.executable, '-m', 'pytest', 'tests/test_integration.py', '-v']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

def run_all_tests():
    """Run all tests with coverage"""
    print("Running all tests with coverage...")
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '--cov=services',
        '--cov-report=html',
        '--cov-report=term-missing',
        '-v'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except FileNotFoundError:
        # pytest-cov not installed, run without coverage
        cmd = [sys.executable, '-m', 'pytest', 'tests/', '-v']
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0

def run_performance_tests():
    """Run performance-focused tests"""
    print("Running performance tests...")
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-m', 'performance',
        '-v',
        '--tb=short'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

def validate_expected_results():
    """Validate that test results match expected outcomes"""
    print("\nValidating expected test results...")
    
    from services.parser import parse_email_content
    from services.rules import analyze_email
    
    fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
    
    # Test cases with expected outcomes
    test_cases = [
        {
            'file': 'safe_newsletter.eml',
            'expected_label': 'Likely Safe',
            'max_score': 29,
            'min_urls': 2
        },
        {
            'file': 'obvious_phishing.eml',
            'expected_label': 'Likely Phishing',
            'min_score': 60,
            'min_evidence': 4
        },
        {
            'file': 'spoofed_display.eml',
            'expected_labels': ['Suspicious', 'Likely Phishing'],
            'min_score': 20,
            'min_evidence': 1
        }
    ]
    
    all_passed = True
    
    for case in test_cases:
        try:
            print(f"  Validating {case['file']}...")
            
            # Load and analyze
            with open(fixtures_dir / case['file'], 'rb') as f:
                email_content = f.read()
            
            parsed = parse_email_content(email_content, case['file'])
            result = analyze_email(parsed)
            
            # Check expected label
            if 'expected_label' in case:
                if result.label != case['expected_label']:
                    print(f"    FAIL: Expected {case['expected_label']}, got {result.label}")
                    all_passed = False
                else:
                    print(f"    PASS: Label {result.label}")
            
            if 'expected_labels' in case:
                if result.label not in case['expected_labels']:
                    print(f"    FAIL: Expected one of {case['expected_labels']}, got {result.label}")
                    all_passed = False
                else:
                    print(f"    PASS: Label {result.label}")
            
            # Check score ranges
            if 'max_score' in case and result.score > case['max_score']:
                print(f"    FAIL: Score {result.score} exceeds maximum {case['max_score']}")
                all_passed = False
            
            if 'min_score' in case and result.score < case['min_score']:
                print(f"    FAIL: Score {result.score} below minimum {case['min_score']}")
                all_passed = False
            
            if 'max_score' in case or 'min_score' in case:
                print(f"    PASS: Score {result.score} in expected range")
            
            # Check evidence count
            if 'min_evidence' in case and len(result.evidence) < case['min_evidence']:
                print(f"    FAIL: Evidence count {len(result.evidence)} below minimum {case['min_evidence']}")
                all_passed = False
            
            # Check URL count
            if 'min_urls' in case and len(parsed.urls) < case['min_urls']:
                print(f"    FAIL: URL count {len(parsed.urls)} below minimum {case['min_urls']}")
                all_passed = False
            
        except Exception as e:
            print(f"    ERROR: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Main test runner"""
    print("=" * 60)
    print("Phase 2 MVP Test Suite")
    print("=" * 60)
    
    start_time = time.time()
    
    # Pre-flight checks
    print("Checking dependencies...")
    if not check_dependencies():
        print("❌ Dependency check failed")
        return 1
    print("✅ Dependencies OK")
    
    print("Checking test fixtures...")
    if not check_fixtures():
        print("❌ Fixture check failed")
        return 1
    print("✅ Fixtures OK")
    
    # Run tests
    test_results = {}
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'parser':
            test_results['parser'] = run_parser_tests()
        elif test_type == 'rules':
            test_results['rules'] = run_rules_tests()
        elif test_type == 'integration':
            test_results['integration'] = run_integration_tests()
        elif test_type == 'performance':
            test_results['performance'] = run_performance_tests()
        elif test_type == 'all':
            test_results['all'] = run_all_tests()
        else:
            print(f"Unknown test type: {test_type}")
            print("Available types: parser, rules, integration, performance, all")
            return 1
    else:
        # Run all tests by default
        test_results['all'] = run_all_tests()
    
    # Validate expected results
    validation_passed = validate_expected_results()
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = all(test_results.values()) and validation_passed
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:15} {status}")
    
    validation_status = "✅ PASS" if validation_passed else "❌ FAIL"
    print(f"{'validation':15} {validation_status}")
    
    print(f"\nTotal time: {duration:.2f}s")
    
    if all_passed:
        print("🎉 All tests passed! Phase 2 MVP is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())