#!/usr/bin/env python3
"""
Create Base Database Schema
Sets up the core tables required by the application before Phase 4 enhancements

This script creates the base schema that the Flask app expects to exist.
"""

import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_PATH = 'data/phishing_analyzer.db'

def ensure_data_directory():
    """Ensure the data directory exists"""
    os.makedirs('data', exist_ok=True)
    logger.info("Data directory ensured")

def create_base_tables(conn):
    """Create base tables required by the Flask application"""
    cursor = conn.cursor()
    
    # Main emails table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            sha256 TEXT NOT NULL UNIQUE,
            parse_summary_json TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Parsed email content table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_parsed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER NOT NULL,
            headers_json TEXT,
            text_body TEXT,
            html_body TEXT,
            html_as_text TEXT,
            urls_json TEXT,
            parse_time_ms INTEGER,
            security_warnings TEXT,
            url_analysis_summary TEXT,  -- Phase 4 enhancement
            FOREIGN KEY (email_id) REFERENCES emails(id)
        )
    """)
    
    # Rule-based detection results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            label TEXT NOT NULL,
            confidence REAL NOT NULL,
            evidence_json TEXT,
            processing_time_ms INTEGER,
            rules_checked INTEGER,
            rules_fired INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email_id) REFERENCES emails(id)
        )
    """)
    
    # AI detection results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            label TEXT NOT NULL,
            evidence_json TEXT,
            tokens_used INTEGER DEFAULT 0,
            cost_estimate REAL DEFAULT 0.0,
            processing_time_ms INTEGER,
            success BOOLEAN DEFAULT 1,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Phase 4 enhancements
            confidence_score REAL,
            explanation TEXT,
            fallback_used BOOLEAN DEFAULT 0,
            prompt_version TEXT,
            analysis_metadata TEXT,
            FOREIGN KEY (email_id) REFERENCES emails(id)
        )
    """)
    
    # AI usage statistics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_usage_stats (
            date TEXT PRIMARY KEY,
            requests_count INTEGER DEFAULT 0,
            tokens_used INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    logger.info("Created base application tables")

def create_indexes(conn):
    """Create indexes for better performance"""
    cursor = conn.cursor()
    
    # Indexes for emails table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_sha256 ON emails(sha256)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_uploaded ON emails(uploaded_at)")
    
    # Indexes for email_parsed table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_parsed_email_id ON email_parsed(email_id)")
    
    # Indexes for detections table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_email_id ON detections(email_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_score ON detections(score)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_created ON detections(created_at)")
    
    # Indexes for ai_detections table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_detections_email_id ON ai_detections(email_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_detections_created ON ai_detections(created_at)")
    
    # Index for ai_usage_stats
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_usage_date ON ai_usage_stats(date)")
    
    logger.info("Created performance indexes")

def check_existing_tables(conn):
    """Check what tables already exist"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"Existing tables: {tables}")
    return tables

def run_base_schema_creation():
    """Run the complete base schema creation"""
    logger.info("Starting base schema creation...")
    
    try:
        # Ensure data directory exists
        ensure_data_directory()
        
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        
        # Check existing structure
        existing_tables = check_existing_tables(conn)
        
        # Create base tables
        create_base_tables(conn)
        
        # Create indexes
        create_indexes(conn)
        
        # Commit all changes
        conn.commit()
        
        # Verify the creation
        final_tables = check_existing_tables(conn)
        new_tables = set(final_tables) - set(existing_tables)
        
        logger.info(f"Base schema creation completed successfully!")
        logger.info(f"Added {len(new_tables)} new tables: {sorted(new_tables)}")
        
        conn.close()
        
        logger.info("Base schema is ready! ✓")
        
        return True
        
    except Exception as e:
        logger.error(f"Base schema creation failed: {e}")
        return False

if __name__ == "__main__":
    success = run_base_schema_creation()
    if success:
        print("\nBase schema created successfully!")
        print("You can now run the Flask application or Phase 4 migration.")
    else:
        print("\nBase schema creation failed. Check the logs above.")