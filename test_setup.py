#!/usr/bin/env python3
"""
Simple test script to verify Phase 1 setup is working correctly
"""

import os
import sqlite3
import hashlib
from datetime import datetime

def test_database():
    """Test database connectivity and structure"""
    print("Testing database...")
    
    db_path = "phishing_detector.db"
    if not os.path.exists(db_path):
        print("❌ Database not found. Run: python init_db.py")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Test table existence
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ['users', 'email_analyses', 'url_analyses', 'system_metrics']
    for table in expected_tables:
        if table in tables:
            print(f"Table '{table}' exists")
        else:
            print(f"Table '{table}' missing")
            return False
    
    # Test insert functionality
    test_hash = hashlib.sha256(b"test email content").hexdigest()
    cursor.execute('''
        INSERT INTO email_analyses (email_hash, filename, file_size, classification, risk_score)
        VALUES (?, ?, ?, ?, ?)
    ''', (test_hash, "test.eml", 1024, "pending", 0))
    
    conn.commit()
    
    # Test query
    cursor.execute("SELECT COUNT(*) FROM email_analyses")
    count = cursor.fetchone()[0]
    print(f"✓ Database insert/query working. Records: {count}")
    
    # Cleanup test record
    cursor.execute("DELETE FROM email_analyses WHERE email_hash = ?", (test_hash,))
    conn.commit()
    conn.close()
    
    return True

def test_environment():
    """Test environment configuration"""
    print("\nTesting environment...")
    
    if os.path.exists('.env'):
        print("✓ .env file exists")
        
        # Check if we can read environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        secret_key = os.getenv('SECRET_KEY')
        if secret_key:
            print("✓ SECRET_KEY loaded from environment")
        else:
            print("❌ SECRET_KEY not found in .env")
            return False
            
    else:
        print("❌ .env file not found. Copy from .env.example")
        return False
    
    return True

def test_file_structure():
    """Test that all required files are present"""
    print("\nTesting file structure...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'Procfile',
        'railway.toml',
        '.gitignore',
        'README.md',
        'templates/base.html',
        'templates/upload.html',
        'templates/stats.html',
        'templates/error.html'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Phase 1 Setup Verification")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    if test_file_structure():
        tests_passed += 1
        print("✅ File structure test PASSED")
    else:
        print("❌ File structure test FAILED")
    
    if test_database():
        tests_passed += 1
        print("✅ Database test PASSED")
    else:
        print("❌ Database test FAILED")
    
    try:
        if test_environment():
            tests_passed += 1
            print("✅ Environment test PASSED")
        else:
            print("❌ Environment test FAILED")
    except ImportError as e:
        print(f"⚠️  Environment test SKIPPED (missing dependency: {e})")
        total_tests -= 1
    
    print(f"\n📊 Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 Phase 1 setup is complete and ready for deployment!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run Flask app: python app.py")
        print("3. Deploy to Railway")
        return True
    else:
        print("❌ Setup incomplete. Please fix the failed tests.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)