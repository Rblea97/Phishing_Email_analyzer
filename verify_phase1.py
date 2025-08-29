#!/usr/bin/env python3
"""
Simple verification script for Phase 1 completion
"""

import os
import sqlite3

def main():
    print("Phase 1 Verification")
    print("=" * 40)
    
    # Check critical files
    files_to_check = [
        'app.py',
        'requirements.txt', 
        'Procfile',
        '.env.example',
        'README.md',
        'phishing_detector.db'
    ]
    
    print("Checking files:")
    all_files_exist = True
    for file in files_to_check:
        if os.path.exists(file):
            print(f"  {file} - OK")
        else:
            print(f"  {file} - MISSING")
            all_files_exist = False
    
    # Check database
    print("\nChecking database:")
    if os.path.exists('phishing_detector.db'):
        try:
            conn = sqlite3.connect('phishing_detector.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['users', 'email_analyses', 'url_analyses', 'system_metrics']
            tables_ok = True
            
            for table in required_tables:
                if table in tables:
                    print(f"  Table {table} - OK")
                else:
                    print(f"  Table {table} - MISSING")
                    tables_ok = False
                    
            conn.close()
            
            if tables_ok:
                print("  Database structure - OK")
            else:
                print("  Database structure - INCOMPLETE")
                all_files_exist = False
                
        except Exception as e:
            print(f"  Database error: {e}")
            all_files_exist = False
    
    # Check Git repository
    print("\nChecking Git:")
    if os.path.exists('.git'):
        print("  Git repository - OK")
    else:
        print("  Git repository - MISSING")
        all_files_exist = False
    
    # Results
    print("\n" + "=" * 40)
    if all_files_exist:
        print("SUCCESS: Phase 1 setup complete!")
        print("\nNext steps:")
        print("1. pip install -r requirements.txt")
        print("2. python app.py")
        print("3. Deploy to Railway")
    else:
        print("INCOMPLETE: Some components missing")
        
    return all_files_exist

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)