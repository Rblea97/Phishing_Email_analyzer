#!/usr/bin/env python3
"""
Phase 4 Database Migration Script
Adds tables and indexes for enhanced detection capabilities

New features:
- URL reputation analysis caching
- Batch processing job tracking
- Performance monitoring
- Enhanced reporting capabilities
"""

import sqlite3
import os
import sys
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

def check_existing_tables(conn):
    """Check what tables already exist"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"Existing tables: {tables}")
    return tables

def create_url_analysis_table(conn):
    """
    Create table for URL reputation analysis caching
    Stores results from Google Safe Browsing and VirusTotal APIs
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS url_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url_hash TEXT NOT NULL UNIQUE,  -- SHA256 hash of URL for privacy
            original_url TEXT NOT NULL,     -- Original URL (for reference)
            is_malicious BOOLEAN NOT NULL DEFAULT 0,
            threat_types TEXT,              -- JSON array of threat types
            confidence_score REAL NOT NULL DEFAULT 0.0,
            analysis_source TEXT NOT NULL,  -- 'google_safe_browsing', 'virustotal', etc.
            analysis_details TEXT,          -- JSON with detailed results
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,           -- When this analysis expires
            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            check_count INTEGER DEFAULT 1   -- How many times this URL was checked
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_analysis_hash ON url_analysis(url_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_analysis_expires ON url_analysis(expires_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_analysis_malicious ON url_analysis(is_malicious)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_analysis_source ON url_analysis(analysis_source)")
    
    logger.info("Created url_analysis table with indexes")

def create_batch_jobs_table(conn):
    """
    Create table for tracking batch processing jobs
    Enables bulk email analysis with progress tracking
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id TEXT PRIMARY KEY,            -- UUID for job tracking
            user_id TEXT,                   -- User identifier (if applicable)
            status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
            total_emails INTEGER NOT NULL DEFAULT 0,
            processed_emails INTEGER NOT NULL DEFAULT 0,
            failed_emails INTEGER NOT NULL DEFAULT 0,
            job_type TEXT NOT NULL DEFAULT 'email_analysis',
            priority INTEGER DEFAULT 0,     -- Job priority (higher = more urgent)
            settings TEXT,                  -- JSON with job settings
            results TEXT,                   -- JSON with aggregated results
            error_message TEXT,             -- Error details if failed
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            estimated_completion TIMESTAMP,  -- Estimated completion time
            worker_id TEXT                  -- Which worker is processing this job
        )
    """)
    
    # Create indexes for job management
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_jobs_status ON batch_jobs(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_jobs_created ON batch_jobs(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_jobs_priority ON batch_jobs(priority DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_jobs_worker ON batch_jobs(worker_id)")
    
    logger.info("Created batch_jobs table with indexes")

def create_batch_job_emails_table(conn):
    """
    Create table for individual emails within batch jobs
    Links batch jobs to specific email analyses
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batch_job_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_job_id TEXT NOT NULL,     -- Reference to batch_jobs.id
            email_analysis_id INTEGER,      -- Reference to email_analysis.id
            original_filename TEXT,         -- Original filename of uploaded email
            file_size INTEGER,              -- Size in bytes
            status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
            error_message TEXT,             -- Error details if processing failed
            processing_time_ms INTEGER,     -- Time taken to process this email
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            FOREIGN KEY (batch_job_id) REFERENCES batch_jobs(id),
            FOREIGN KEY (email_analysis_id) REFERENCES email_analysis(id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_job_emails_job_id ON batch_job_emails(batch_job_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_job_emails_status ON batch_job_emails(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_job_emails_analysis_id ON batch_job_emails(email_analysis_id)")
    
    logger.info("Created batch_job_emails table with indexes")

def create_performance_metrics_table(conn):
    """
    Create table for performance monitoring and benchmarking
    Tracks system performance over time
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_type TEXT NOT NULL,      -- 'analysis_time', 'memory_usage', 'api_latency', etc.
            metric_name TEXT NOT NULL,      -- Specific metric name
            value REAL NOT NULL,            -- Metric value
            unit TEXT,                      -- Unit of measurement ('ms', 'bytes', '%', etc.)
            component TEXT,                 -- Which component generated this metric
            context TEXT,                   -- JSON with additional context
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT                 -- Group related metrics by session
        )
    """)
    
    # Create indexes for querying performance data
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_metrics_recorded ON performance_metrics(recorded_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_metrics_component ON performance_metrics(component)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_metrics_session ON performance_metrics(session_id)")
    
    logger.info("Created performance_metrics table with indexes")

def create_export_requests_table(conn):
    """
    Create table for tracking report export requests
    Enables async report generation and download tracking
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS export_requests (
            id TEXT PRIMARY KEY,            -- UUID for export tracking
            user_id TEXT,                   -- User identifier
            export_type TEXT NOT NULL,      -- 'pdf', 'json', 'csv', 'excel'
            data_type TEXT NOT NULL,        -- 'single_analysis', 'batch_results', 'performance_report'
            reference_id TEXT NOT NULL,     -- ID of what's being exported
            status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'generating', 'completed', 'failed'
            file_path TEXT,                 -- Path to generated file
            file_size INTEGER,              -- Size in bytes
            settings TEXT,                  -- JSON with export settings
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            expires_at TIMESTAMP,           -- When the exported file will be deleted
            download_count INTEGER DEFAULT 0,
            last_downloaded TIMESTAMP
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_export_requests_status ON export_requests(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_export_requests_created ON export_requests(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_export_requests_expires ON export_requests(expires_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_export_requests_type ON export_requests(export_type)")
    
    logger.info("Created export_requests table with indexes")

def enhance_existing_tables(conn):
    """
    Add Phase 4 enhancements to existing tables
    """
    cursor = conn.cursor()
    
    # Add URL analysis reference to email_analysis table
    try:
        cursor.execute("ALTER TABLE email_analysis ADD COLUMN url_analysis_summary TEXT")
        logger.info("Added url_analysis_summary column to email_analysis table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            logger.warning(f"Could not add url_analysis_summary column: {e}")

    # Add performance tracking columns
    try:
        cursor.execute("ALTER TABLE email_analysis ADD COLUMN processing_time_ms INTEGER")
        logger.info("Added processing_time_ms column to email_analysis table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            logger.warning(f"Could not add processing_time_ms column: {e}")

    try:
        cursor.execute("ALTER TABLE email_analysis ADD COLUMN cache_hit_rate REAL")
        logger.info("Added cache_hit_rate column to email_analysis table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            logger.warning(f"Could not add cache_hit_rate column: {e}")

    # Add enhanced AI analysis columns
    try:
        cursor.execute("ALTER TABLE email_analysis ADD COLUMN ai_explanation TEXT")
        logger.info("Added ai_explanation column to email_analysis table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            logger.warning(f"Could not add ai_explanation column: {e}")

    try:
        cursor.execute("ALTER TABLE email_analysis ADD COLUMN confidence_calibration REAL")
        logger.info("Added confidence_calibration column to email_analysis table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            logger.warning(f"Could not add confidence_calibration column: {e}")

def create_views_for_reporting(conn):
    """
    Create database views for easier reporting and analytics
    """
    cursor = conn.cursor()
    
    # View for batch job summary statistics
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS batch_job_summary AS
        SELECT 
            bj.id,
            bj.status,
            bj.total_emails,
            bj.processed_emails,
            bj.failed_emails,
            ROUND((CAST(bj.processed_emails AS REAL) / bj.total_emails) * 100, 2) as completion_percentage,
            bj.created_at,
            bj.completed_at,
            CASE 
                WHEN bj.completed_at IS NOT NULL AND bj.started_at IS NOT NULL 
                THEN ROUND((julianday(bj.completed_at) - julianday(bj.started_at)) * 86400000)
                ELSE NULL 
            END as total_processing_time_ms
        FROM batch_jobs bj
    """)
    
    # View for performance analytics
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS performance_summary AS
        SELECT 
            metric_type,
            metric_name,
            component,
            COUNT(*) as measurement_count,
            AVG(value) as avg_value,
            MIN(value) as min_value,
            MAX(value) as max_value,
            ROUND(value * 0.95) as p95_value,  -- Approximate 95th percentile
            unit,
            DATE(recorded_at) as date
        FROM performance_metrics
        GROUP BY metric_type, metric_name, component, DATE(recorded_at)
    """)
    
    # View for malicious URL statistics
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS url_threat_summary AS
        SELECT 
            analysis_source,
            COUNT(*) as total_urls_analyzed,
            SUM(CASE WHEN is_malicious = 1 THEN 1 ELSE 0 END) as malicious_urls,
            AVG(confidence_score) as avg_confidence,
            DATE(created_at) as analysis_date
        FROM url_analysis
        GROUP BY analysis_source, DATE(created_at)
    """)
    
    logger.info("Created reporting views")

def run_migration():
    """Run the complete Phase 4 migration"""
    logger.info("Starting Phase 4 database migration...")
    
    try:
        # Ensure data directory exists
        ensure_data_directory()
        
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        
        # Check existing structure
        existing_tables = check_existing_tables(conn)
        
        # Create new tables
        create_url_analysis_table(conn)
        create_batch_jobs_table(conn)
        create_batch_job_emails_table(conn)
        create_performance_metrics_table(conn)
        create_export_requests_table(conn)
        
        # Enhance existing tables
        enhance_existing_tables(conn)
        
        # Create reporting views
        create_views_for_reporting(conn)
        
        # Commit all changes
        conn.commit()
        
        # Verify the migration
        final_tables = check_existing_tables(conn)
        new_tables = set(final_tables) - set(existing_tables)
        
        logger.info(f"Migration completed successfully!")
        logger.info(f"Added {len(new_tables)} new tables: {sorted(new_tables)}")
        
        # Insert a test performance metric to verify the setup
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO performance_metrics 
            (metric_type, metric_name, value, unit, component, context)
            VALUES ('migration', 'phase4_migration_success', 1, 'boolean', 'migration_script', '{"version": "4.0", "timestamp": "' + ? + '"}')
        """, (datetime.now().isoformat(),))
        conn.commit()
        
        conn.close()
        
        logger.info("Phase 4 migration completed successfully! 🚀")
        logger.info("New capabilities enabled:")
        logger.info("  ✓ URL reputation analysis with caching")
        logger.info("  ✓ Batch processing job tracking") 
        logger.info("  ✓ Performance monitoring and metrics")
        logger.info("  ✓ Export request management")
        logger.info("  ✓ Enhanced reporting views")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)