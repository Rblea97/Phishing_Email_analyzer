#!/usr/bin/env python3
"""
Database Migration Script for Phase 2 MVP
Adds new tables for email parsing and detection results
"""

import os
import sqlite3
from datetime import datetime

def migrate_database(db_path="phishing_detector.db"):
    """Migrate database to Phase 2 schema"""
    
    print(f"Migrating database to Phase 2: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        print("Please run: python init_db.py first")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current schema version
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        
        # Check if Phase 2 migration already applied
        cursor.execute("SELECT version FROM schema_versions WHERE version = 2")
        if cursor.fetchone():
            print("Phase 2 migration already applied")
            return True
        
        print("Applying Phase 2 schema changes...")
        
        # Create emails table (new structure for Phase 2)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                filename VARCHAR(255) NOT NULL,
                size_bytes INTEGER NOT NULL,
                sha256 VARCHAR(64) UNIQUE NOT NULL,
                parse_summary_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Created emails table")
        
        # Create email_parsed table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_parsed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER NOT NULL,
                headers_json TEXT NOT NULL,
                text_body TEXT,
                html_body TEXT,
                html_as_text TEXT,
                urls_json TEXT,
                parse_time_ms REAL,
                security_warnings TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES emails (id)
            )
        ''')
        print("Created email_parsed table")
        
        # Create detections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                label VARCHAR(50) NOT NULL,
                confidence REAL NOT NULL,
                evidence_json TEXT NOT NULL,
                processing_time_ms REAL,
                rules_checked INTEGER,
                rules_fired INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES emails (id)
            )
        ''')
        print("Created detections table")
        
        # Create performance indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_emails_uploaded_at ON emails (uploaded_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_emails_sha256 ON emails (sha256)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_email_parsed_email_id ON email_parsed (email_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_detections_email_id ON detections (email_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_detections_score ON detections (score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_detections_created_at ON detections (created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_detections_label ON detections (label)')
        print("Created performance indexes")
        
        # Migrate existing email_analyses data to new structure
        cursor.execute("SELECT COUNT(*) FROM email_analyses")
        old_count = cursor.fetchone()[0]
        
        if old_count > 0:
            print(f"Migrating {old_count} existing records...")
            
            # Get old records
            cursor.execute('''
                SELECT id, email_hash, filename, file_size, created_at, 
                       classification, risk_score, confidence
                FROM email_analyses
            ''')
            
            old_records = cursor.fetchall()
            migrated_count = 0
            
            for record in old_records:
                old_id, email_hash, filename, file_size, created_at, classification, risk_score, confidence = record
                
                try:
                    # Insert into emails table
                    cursor.execute('''
                        INSERT OR IGNORE INTO emails (filename, size_bytes, sha256, uploaded_at)
                        VALUES (?, ?, ?, ?)
                    ''', (filename, file_size or 0, email_hash, created_at))
                    
                    # Get the email_id
                    cursor.execute('SELECT id FROM emails WHERE sha256 = ?', (email_hash,))
                    email_id = cursor.fetchone()[0]
                    
                    # Insert placeholder parsed data
                    cursor.execute('''
                        INSERT OR IGNORE INTO email_parsed (
                            email_id, headers_json, text_body, parse_time_ms
                        ) VALUES (?, ?, ?, ?)
                    ''', (email_id, '{"migrated": true}', 'Migrated from Phase 1', 0))
                    
                    # Insert detection data if available
                    if risk_score is not None:
                        evidence_json = f'{{"evidence": [], "note": "Migrated from Phase 1"}}'
                        cursor.execute('''
                            INSERT OR IGNORE INTO detections (
                                email_id, score, label, confidence, evidence_json,
                                processing_time_ms, rules_checked, rules_fired
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            email_id, 
                            risk_score or 0,
                            classification or 'Unknown',
                            confidence or 0.0,
                            evidence_json,
                            0, 0, 0
                        ))
                    
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"Warning: Failed to migrate record {old_id}: {e}")
                    continue
            
            print(f"Successfully migrated {migrated_count} records")
        
        # Record migration
        cursor.execute('''
            INSERT INTO schema_versions (version, description)
            VALUES (2, "Phase 2 MVP: Added emails, email_parsed, and detections tables")
        ''')
        
        # Update system metrics with new structure info
        cursor.execute('''
            INSERT OR REPLACE INTO system_metrics 
            (date, total_analyses, phishing_detected, accuracy_rate, avg_processing_time, api_costs)
            VALUES (date('now'), 
                    (SELECT COUNT(*) FROM emails),
                    (SELECT COUNT(*) FROM detections WHERE label = 'Likely Phishing'),
                    0.0, 0.0, 0.0)
        ''')
        
        conn.commit()
        print("\nPhase 2 migration completed successfully!")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM emails")
        emails_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM email_parsed")
        parsed_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM detections")
        detections_count = cursor.fetchone()[0]
        
        print(f"Database summary:")
        print(f"  - Emails: {emails_count}")
        print(f"  - Parsed records: {parsed_count}")
        print(f"  - Detection results: {detections_count}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {str(e)}")
        return False
        
    finally:
        conn.close()

def verify_phase2_schema(db_path="phishing_detector.db"):
    """Verify Phase 2 database schema"""
    
    print(f"Verifying Phase 2 schema: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check required tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['emails', 'email_parsed', 'detections', 'schema_versions']
        
        print("Checking required tables:")
        all_present = True
        for table in required_tables:
            if table in tables:
                print(f"  {table} - OK")
            else:
                print(f"  {table} - MISSING")
                all_present = False
        
        if not all_present:
            return False
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        required_indexes = [
            'ix_emails_uploaded_at', 'ix_emails_sha256',
            'ix_detections_score', 'ix_detections_created_at'
        ]
        
        print("Checking performance indexes:")
        for index in required_indexes:
            if index in indexes:
                print(f"  {index} - OK")
            else:
                print(f"  {index} - MISSING")
        
        # Check schema version
        cursor.execute("SELECT version, description FROM schema_versions WHERE version = 2")
        result = cursor.fetchone()
        
        if result:
            print(f"\nSchema version: {result[0]} - {result[1]}")
            print("Phase 2 schema verified successfully!")
            return True
        else:
            print("\nPhase 2 migration not found in schema_versions")
            return False
            
    except Exception as e:
        print(f"Schema verification failed: {str(e)}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    
    # Get database path from command line or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else "phishing_detector.db"
    
    print("=" * 60)
    print("AI-Powered Phishing Detection - Phase 2 Migration")
    print("=" * 60)
    
    try:
        # Run migration
        success = migrate_database(db_path)
        
        if success:
            # Verify schema
            verify_phase2_schema(db_path)
            
            print("\nReady for Phase 2 development!")
            print("Next steps:")
            print("1. pip install html2text email-validator")
            print("2. Test with: python -c 'from services.parser import parse_email_content'")
            print("3. Run Flask app: python app.py")
        else:
            print("\nMigration failed. Please check error messages above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)