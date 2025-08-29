#!/usr/bin/env python3
"""
Database initialization script for AI-Powered Phishing Detection System
Run this script to create the SQLite database schema
"""

import os
import sqlite3
from datetime import datetime

def create_database(db_path="phishing_detector.db"):
    """Create SQLite database with required schema"""
    
    print(f"Creating database: {db_path}")
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    # Connect to database (creates file if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating tables...")
    
    # Create users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            api_key VARCHAR(64) UNIQUE,
            daily_usage INTEGER DEFAULT 0,
            daily_limit INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    print("✓ Created users table")
    
    # Create email analyses table
    cursor.execute('''
        CREATE TABLE email_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email_hash VARCHAR(64) NOT NULL,
            filename VARCHAR(255),
            file_size INTEGER,
            analysis_result JSON,
            risk_score INTEGER,
            classification VARCHAR(20),
            confidence FLOAT,
            processing_time FLOAT,
            model_version VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    print("✓ Created email_analyses table")
    
    # Create URL analyses cache table
    cursor.execute('''
        CREATE TABLE url_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url_hash VARCHAR(64) UNIQUE NOT NULL,
            url TEXT NOT NULL,
            safe_browsing_result JSON,
            urlvoid_result JSON,
            risk_score INTEGER,
            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')
    print("✓ Created url_analyses table")
    
    # Create system metrics table
    cursor.execute('''
        CREATE TABLE system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            total_analyses INTEGER DEFAULT 0,
            phishing_detected INTEGER DEFAULT 0,
            accuracy_rate FLOAT,
            avg_processing_time FLOAT,
            api_costs FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ Created system_metrics table")
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX ix_email_analyses_created_at ON email_analyses (created_at)')
    cursor.execute('CREATE INDEX ix_email_analyses_email_hash ON email_analyses (email_hash)')
    cursor.execute('CREATE INDEX ix_url_analyses_url_hash ON url_analyses (url_hash)')
    cursor.execute('CREATE INDEX ix_system_metrics_date ON system_metrics (date)')
    print("✓ Created database indexes")
    
    # Insert sample data for testing
    cursor.execute('''
        INSERT INTO system_metrics (date, total_analyses, phishing_detected, accuracy_rate, avg_processing_time, api_costs)
        VALUES (date('now'), 0, 0, 0.0, 0.0, 0.0)
    ''')
    print("✓ Inserted initial system metrics")
    
    # Commit changes and close
    conn.commit()
    conn.close()
    
    print(f"\n✅ Database created successfully: {db_path}")
    print(f"   Tables: users, email_analyses, url_analyses, system_metrics")
    print(f"   Indexes: Performance optimized")
    print(f"   Ready for Phase 1 deployment!")

def verify_database(db_path="phishing_detector.db"):
    """Verify database structure"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    print(f"\n🔍 Verifying database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    expected_tables = ['users', 'email_analyses', 'url_analyses', 'system_metrics']
    found_tables = [table[0] for table in tables]
    
    print(f"   Expected tables: {expected_tables}")
    print(f"   Found tables: {found_tables}")
    
    # Check if all expected tables exist
    missing_tables = set(expected_tables) - set(found_tables)
    if missing_tables:
        print(f"   ❌ Missing tables: {missing_tables}")
        return False
    
    # Check table structures
    for table in expected_tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print(f"   ✓ {table}: {len(columns)} columns")
    
    conn.close()
    print("   ✅ Database structure verified!")
    return True

if __name__ == "__main__":
    import sys
    
    # Get database path from command line or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else "phishing_detector.db"
    
    print("=" * 60)
    print("AI-Powered Phishing Detection - Database Initialization")
    print("=" * 60)
    
    try:
        # Create database
        create_database(db_path)
        
        # Verify creation
        verify_database(db_path)
        
        print("\n🚀 Ready to run Flask application!")
        print(f"   Run: python app.py")
        print(f"   Or: flask run")
        
    except Exception as e:
        print(f"\n❌ Error creating database: {str(e)}")
        sys.exit(1)