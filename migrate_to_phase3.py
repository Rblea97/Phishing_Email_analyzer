"""
Database Migration Script: Phase 2 → Phase 3 (AI Integration)

Adds ai_detections table for storing GPT-4o-mini analysis results
while preserving all existing Phase 2 data and schema.
"""

import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_PATH = 'phishing_detector.db'


def get_db_version():
    """Get current database version"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if version table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_version'
        """)
        
        if cursor.fetchone() is None:
            # No version table, assume Phase 2
            conn.close()
            return 2
        
        cursor.execute("SELECT version FROM schema_version ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 2
        
    except Exception as e:
        logger.error(f"Failed to get database version: {e}")
        return 2


def create_version_table(conn):
    """Create schema version tracking table"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert Phase 2 record if this is the first migration
    cursor.execute("""
        INSERT INTO schema_version (version, description)
        SELECT 2, 'Phase 2: Rule-based detection with email parsing'
        WHERE NOT EXISTS (SELECT 1 FROM schema_version WHERE version = 2)
    """)
    
    conn.commit()
    logger.info("Schema version table created/updated")


def create_ai_detections_table(conn):
    """Create ai_detections table for AI analysis results"""
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE ai_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER NOT NULL,
            score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
            label TEXT NOT NULL CHECK (label IN ('Likely Safe', 'Suspicious', 'Likely Phishing')),
            evidence_json TEXT NOT NULL,
            tokens_used INTEGER NOT NULL DEFAULT 0,
            cost_estimate REAL NOT NULL DEFAULT 0.0,
            processing_time_ms REAL NOT NULL DEFAULT 0.0,
            success BOOLEAN NOT NULL DEFAULT 1,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email_id) REFERENCES emails (id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX idx_ai_detections_email_id ON ai_detections(email_id)")
    cursor.execute("CREATE INDEX idx_ai_detections_created_at ON ai_detections(created_at)")
    cursor.execute("CREATE INDEX idx_ai_detections_score ON ai_detections(score)")
    cursor.execute("CREATE INDEX idx_ai_detections_success ON ai_detections(success)")
    
    conn.commit()
    logger.info("ai_detections table created with indexes")


def create_ai_usage_stats_table(conn):
    """Create table for tracking daily AI usage and costs"""
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE ai_usage_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL UNIQUE,
            requests_count INTEGER NOT NULL DEFAULT 0,
            tokens_used INTEGER NOT NULL DEFAULT 0,
            total_cost REAL NOT NULL DEFAULT 0.0,
            avg_processing_time_ms REAL,
            success_rate REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX idx_ai_usage_stats_date ON ai_usage_stats(date)")
    
    conn.commit()
    logger.info("ai_usage_stats table created")


def verify_existing_schema(conn):
    """Verify that Phase 2 schema exists and is intact"""
    cursor = conn.cursor()
    
    # Check that all Phase 2 tables exist
    required_tables = ['emails', 'email_parsed', 'detections']
    
    for table in required_tables:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table,))
        
        if cursor.fetchone() is None:
            raise Exception(f"Required Phase 2 table '{table}' not found. Run Phase 2 migration first.")
    
    # Check that Phase 2 tables have expected columns (based on actual Phase 2 schema)
    cursor.execute("PRAGMA table_info(emails)")
    email_columns = {row[1] for row in cursor.fetchall()}
    expected_email_columns = {'id', 'uploaded_at', 'filename', 'size_bytes', 'sha256', 'parse_summary_json', 'created_at'}
    
    if not expected_email_columns.issubset(email_columns):
        missing = expected_email_columns - email_columns
        raise Exception(f"Phase 2 emails table missing columns: {missing}")
    
    # Check detections table
    cursor.execute("PRAGMA table_info(detections)")
    detection_columns = {row[1] for row in cursor.fetchall()}
    expected_detection_columns = {'id', 'email_id', 'score', 'label', 'confidence', 'evidence_json', 'processing_time_ms', 'rules_checked', 'rules_fired', 'created_at'}
    
    if not expected_detection_columns.issubset(detection_columns):
        missing = expected_detection_columns - detection_columns
        raise Exception(f"Phase 2 detections table missing columns: {missing}")
    
    logger.info("Phase 2 schema verification passed")


def migrate_to_phase3():
    """Execute Phase 3 migration"""
    
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        logger.error(f"Database {DATABASE_PATH} not found. Run Phase 2 setup first.")
        return False
    
    try:
        # Get current version
        current_version = get_db_version()
        logger.info(f"Current database version: {current_version}")
        
        if current_version >= 3:
            logger.info("Database is already at Phase 3 or higher")
            return True
        
        if current_version < 2:
            logger.error("Database is not at Phase 2. Run Phase 2 migration first.")
            return False
        
        # Start migration
        logger.info("Starting Phase 3 migration...")
        
        # Create backup
        backup_path = f"{DATABASE_PATH}.phase2_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(DATABASE_PATH, backup_path)
        logger.info(f"Backup created: {backup_path}")
        
        # Connect and begin transaction
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute("BEGIN")
        
        try:
            # Verify Phase 2 schema
            verify_existing_schema(conn)
            
            # Create version table
            create_version_table(conn)
            
            # Create new Phase 3 tables
            create_ai_detections_table(conn)
            create_ai_usage_stats_table(conn)
            
            # Update schema version
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO schema_version (version, description)
                VALUES (3, 'Phase 3: AI integration with GPT-4o-mini')
            """)
            
            # Commit transaction
            conn.commit()
            logger.info("Phase 3 migration completed successfully")
            
            # Verify migration
            verify_phase3_schema(conn)
            
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Migration failed, rolling back: {e}")
            return False
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def verify_phase3_schema(conn):
    """Verify Phase 3 schema is correct"""
    cursor = conn.cursor()
    
    # Check new tables exist
    new_tables = ['ai_detections', 'ai_usage_stats', 'schema_version']
    
    for table in new_tables:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table,))
        
        if cursor.fetchone() is None:
            raise Exception(f"Phase 3 table '{table}' not created")
    
    # Check ai_detections columns
    cursor.execute("PRAGMA table_info(ai_detections)")
    ai_columns = {row[1] for row in cursor.fetchall()}
    expected_ai_columns = {
        'id', 'email_id', 'score', 'label', 'evidence_json', 
        'tokens_used', 'cost_estimate', 'processing_time_ms',
        'success', 'error_message', 'created_at'
    }
    
    if not expected_ai_columns.issubset(ai_columns):
        missing = expected_ai_columns - ai_columns
        raise Exception(f"ai_detections table missing columns: {missing}")
    
    # Verify indexes exist
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND tbl_name='ai_detections'
    """)
    indexes = {row[0] for row in cursor.fetchall()}
    expected_indexes = {
        'idx_ai_detections_email_id',
        'idx_ai_detections_created_at', 
        'idx_ai_detections_score',
        'idx_ai_detections_success'
    }
    
    if not expected_indexes.issubset(indexes):
        missing = expected_indexes - indexes
        raise Exception(f"ai_detections indexes missing: {missing}")
    
    logger.info("Phase 3 schema verification passed")


def get_schema_info():
    """Display current schema information"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("\n=== DATABASE SCHEMA INFORMATION ===")
        print(f"Database: {DATABASE_PATH}")
        
        # Get version
        version = get_db_version()
        print(f"Schema Version: {version}")
        
        # List tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables: {', '.join(tables)}")
        
        # Show schema version history if available
        if 'schema_version' in tables:
            cursor.execute("""
                SELECT version, description, created_at 
                FROM schema_version 
                ORDER BY version
            """)
            print("\nSchema History:")
            for row in cursor.fetchall():
                print(f"  v{row[0]}: {row[1]} ({row[2]})")
        
        # Show record counts
        print("\nRecord Counts:")
        for table in tables:
            if table != 'sqlite_sequence' and not table.startswith('sqlite_'):
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} records")
        
        conn.close()
        print("=" * 40)
        
    except Exception as e:
        print(f"Error getting schema info: {e}")


if __name__ == "__main__":
    print("Phase 3 Database Migration Script")
    print("Adds AI integration tables to existing Phase 2 schema")
    
    # Show current schema
    get_schema_info()
    
    # Confirm migration
    response = input("\nProceed with Phase 3 migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled")
        exit(0)
    
    # Execute migration
    success = migrate_to_phase3()
    
    if success:
        print("\n✓ Phase 3 migration completed successfully!")
        get_schema_info()
    else:
        print("\n✗ Phase 3 migration failed. Check logs for details.")
        exit(1)