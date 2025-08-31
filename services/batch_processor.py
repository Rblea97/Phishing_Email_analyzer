"""
Batch Processing Service - Phase 4 Enhancement
Celery-based async processing for bulk email analysis

Provides scalable background processing for analyzing multiple emails
with progress tracking, result aggregation, and error handling.
"""

import os
import json
import uuid
import sqlite3
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import tempfile
import zipfile

# Celery imports
try:
    from celery import Celery
    from celery.result import AsyncResult
    from celery import signals
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

# Import our core services
from services.parser import parse_email_content, EmailParsingError
from services.rules import analyze_email
from services.ai import analyze_email_with_ai

logger = logging.getLogger(__name__)

@dataclass
class BatchJobConfig:
    """Configuration for batch processing jobs"""
    enable_ai_analysis: bool = True
    enable_url_reputation: bool = True
    max_file_size_mb: int = 25
    timeout_per_email_seconds: int = 60
    priority: int = 0  # Higher = more urgent
    user_id: Optional[str] = None
    notification_email: Optional[str] = None
    export_format: str = 'json'  # 'json', 'pdf', 'csv'

@dataclass
class BatchJobResult:
    """Results from a batch processing job"""
    job_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    total_emails: int
    processed_emails: int
    failed_emails: int
    results: List[Dict] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None

class BatchProcessingError(Exception):
    """Custom exception for batch processing errors"""
    pass

# Initialize Celery app
def create_celery_app() -> Optional['Celery']:
    """Create and configure Celery application"""
    if not CELERY_AVAILABLE:
        logger.warning("Celery not available - batch processing will be limited")
        return None
        
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    app = Celery('phishing_batch_processor')
    
    # Configure Celery
    app.conf.update(
        broker_url=redis_url,
        result_backend=redis_url,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,  # Process one task at a time for better progress tracking
        task_acks_late=True,
        worker_disable_rate_limits=False,
        task_routes={
            'services.batch_processor.process_single_email': {'queue': 'email_processing'},
            'services.batch_processor.process_batch_job': {'queue': 'batch_jobs'},
        }
    )
    
    return app

# Global Celery app instance
celery_app = create_celery_app()

class BatchProcessor:
    """
    Main batch processing service
    Manages bulk email analysis with Celery background workers
    """
    
    def __init__(self):
        self.db_path = os.getenv('DATABASE_PATH', 'data/phishing_analyzer.db')
        self.upload_dir = Path(os.getenv('UPLOAD_DIR', 'data/uploads'))
        self.results_dir = Path(os.getenv('RESULTS_DIR', 'data/results'))
        
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"BatchProcessor initialized with DB: {self.db_path}")

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn

    def create_batch_job(self, 
                        email_files: List[Tuple[str, bytes]], 
                        config: BatchJobConfig) -> str:
        """
        Create a new batch processing job
        
        Args:
            email_files: List of (filename, file_content) tuples
            config: Job configuration
            
        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())
        
        try:
            # Store files in upload directory
            job_upload_dir = self.upload_dir / job_id
            job_upload_dir.mkdir(exist_ok=True)
            
            stored_files = []
            for filename, content in email_files:
                # Sanitize filename
                safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                file_path = job_upload_dir / safe_filename
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                stored_files.append({
                    'original_filename': filename,
                    'stored_path': str(file_path),
                    'file_size': len(content)
                })
            
            # Create database record
            conn = self._get_db_connection()
            try:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO batch_jobs 
                    (id, status, total_emails, processed_emails, failed_emails, 
                     priority, settings, created_at)
                    VALUES (?, ?, ?, 0, 0, ?, ?, ?)
                """, (
                    job_id, 'pending', len(email_files),
                    config.priority, json.dumps(asdict(config)),
                    datetime.now().isoformat()
                ))
                
                # Create individual email records
                for file_info in stored_files:
                    cursor.execute("""
                        INSERT INTO batch_job_emails
                        (batch_job_id, original_filename, file_size, status)
                        VALUES (?, ?, ?, 'pending')
                    """, (job_id, file_info['original_filename'], file_info['file_size']))
                
                conn.commit()
                
                # Submit to Celery if available
                if celery_app and CELERY_AVAILABLE:
                    process_batch_job.delay(job_id, stored_files, asdict(config))
                    logger.info(f"Batch job {job_id} submitted to Celery with {len(email_files)} emails")
                else:
                    # Process synchronously as fallback
                    logger.warning("Celery not available, processing batch job synchronously")
                    self._process_batch_synchronously(job_id, stored_files, config)
                
                return job_id
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Failed to create batch job: {e}")
            raise BatchProcessingError(f"Job creation failed: {e}")

    def _process_batch_synchronously(self, job_id: str, files: List[Dict], config: BatchJobConfig):
        """
        Fallback synchronous processing when Celery is not available
        """
        try:
            self._update_job_status(job_id, 'processing')
            
            results = []
            processed = 0
            failed = 0
            
            for file_info in files:
                try:
                    result = self._process_single_email_sync(
                        file_info['stored_path'], 
                        file_info['original_filename'],
                        config
                    )
                    results.append(result)
                    processed += 1
                    
                    # Update progress
                    self._update_job_progress(job_id, processed, failed)
                    
                except Exception as e:
                    logger.error(f"Failed to process {file_info['original_filename']}: {e}")
                    failed += 1
                    self._update_job_progress(job_id, processed, failed)
            
            # Mark job as completed
            self._complete_job(job_id, results)
            
        except Exception as e:
            logger.error(f"Batch job {job_id} failed: {e}")
            self._update_job_status(job_id, 'failed', str(e))

    def _process_single_email_sync(self, file_path: str, filename: str, config: BatchJobConfig) -> Dict:
        """Process a single email file synchronously"""
        start_time = time.time()
        
        try:
            # Read and parse email
            with open(file_path, 'rb') as f:
                email_content = f.read()
            
            email_hash = self._get_file_hash(email_content)
            parsed_email = parse_email_content(email_content)
            
            # Rule-based analysis
            rule_analysis = analyze_email(parsed_email)
            
            result = {
                'filename': filename,
                'email_hash': email_hash,
                'status': 'completed',
                'rule_analysis': asdict(rule_analysis),
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
            
            # AI analysis if enabled
            if config.enable_ai_analysis:
                try:
                    ai_analysis = analyze_email_with_ai(parsed_email)
                    result['ai_analysis'] = asdict(ai_analysis)
                except Exception as e:
                    logger.warning(f"AI analysis failed for {filename}: {e}")
                    result['ai_analysis'] = {'error': str(e)}
            
            # URL reputation if enabled
            if config.enable_url_reputation and parsed_email.urls:
                try:
                    from services.url_reputation import get_url_reputation_service
                    url_service = get_url_reputation_service()
                    url_results = url_service.analyze_urls(parsed_email.urls)
                    result['url_analysis'] = {
                        url: asdict(analysis) for url, analysis in url_results.items()
                    }
                except Exception as e:
                    logger.warning(f"URL analysis failed for {filename}: {e}")
                    result['url_analysis'] = {'error': str(e)}
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process email {filename}: {e}")
            return {
                'filename': filename,
                'status': 'failed',
                'error': str(e),
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }

    def _get_file_hash(self, content: bytes) -> str:
        """Generate hash for email content"""
        import hashlib
        return hashlib.sha256(content).hexdigest()

    def _update_job_status(self, job_id: str, status: str, error_message: Optional[str] = None):
        """Update job status in database"""
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            
            update_fields = ["status = ?"]
            values = [status]
            
            if status == 'processing' and not error_message:
                update_fields.append("started_at = ?")
                values.append(datetime.now().isoformat())
            elif status in ['completed', 'failed']:
                update_fields.append("completed_at = ?")
                values.append(datetime.now().isoformat())
            
            if error_message:
                update_fields.append("error_message = ?")
                values.append(error_message)
            
            values.append(job_id)
            
            cursor.execute(f"""
                UPDATE batch_jobs 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, values)
            
            conn.commit()
            
        finally:
            conn.close()

    def _update_job_progress(self, job_id: str, processed: int, failed: int):
        """Update job progress counters"""
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE batch_jobs 
                SET processed_emails = ?, failed_emails = ?
                WHERE id = ?
            """, (processed, failed, job_id))
            conn.commit()
        finally:
            conn.close()

    def _complete_job(self, job_id: str, results: List[Dict]):
        """Complete a batch job with results"""
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Store results summary
            results_summary = {
                'total_processed': len(results),
                'successful': len([r for r in results if r['status'] == 'completed']),
                'failed': len([r for r in results if r['status'] == 'failed']),
                'results': results[:100]  # Store only first 100 for database size
            }
            
            cursor.execute("""
                UPDATE batch_jobs 
                SET status = 'completed', 
                    completed_at = ?,
                    results = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), json.dumps(results_summary), job_id))
            
            conn.commit()
            
            # Save full results to file
            results_file = self.results_dir / f"{job_id}_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Batch job {job_id} completed with {len(results)} results")
            
        finally:
            conn.close()

    def get_job_status(self, job_id: str) -> Optional[BatchJobResult]:
        """Get current status of a batch job"""
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM batch_jobs WHERE id = ?
            """, (job_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return BatchJobResult(
                job_id=row['id'],
                status=row['status'],
                total_emails=row['total_emails'],
                processed_emails=row['processed_emails'],
                failed_emails=row['failed_emails'],
                error_message=row['error_message'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None
            )
            
        finally:
            conn.close()

    def get_job_results(self, job_id: str) -> Optional[List[Dict]]:
        """Get detailed results for a completed job"""
        results_file = self.results_dir / f"{job_id}_results.json"
        
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read results file for {job_id}: {e}")
        
        # Fall back to database results (limited)
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT results FROM batch_jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            
            if row and row['results']:
                results_data = json.loads(row['results'])
                return results_data.get('results', [])
                
        finally:
            conn.close()
        
        return None

    def list_jobs(self, limit: int = 50, status: Optional[str] = None) -> List[BatchJobResult]:
        """List recent batch jobs"""
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            
            query = "SELECT * FROM batch_jobs"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                results.append(BatchJobResult(
                    job_id=row['id'],
                    status=row['status'],
                    total_emails=row['total_emails'],
                    processed_emails=row['processed_emails'],
                    failed_emails=row['failed_emails'],
                    error_message=row['error_message'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None
                ))
            
            return results
            
        finally:
            conn.close()

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running batch job"""
        try:
            # Update database status
            conn = self._get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE batch_jobs 
                    SET status = 'cancelled', completed_at = ?
                    WHERE id = ? AND status IN ('pending', 'processing')
                """, (datetime.now().isoformat(), job_id))
                
                updated = cursor.rowcount > 0
                conn.commit()
                
                if updated:
                    logger.info(f"Batch job {job_id} cancelled")
                
                return updated
                
            finally:
                conn.close()
                
            # TODO: Also cancel Celery task if running
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False


# Celery tasks
if CELERY_AVAILABLE and celery_app:
    
    @celery_app.task(bind=True)
    def process_batch_job(self, job_id: str, files: List[Dict], config: Dict):
        """Celery task to process a batch job"""
        try:
            logger.info(f"Starting Celery batch job {job_id}")
            
            # Update job status
            processor = BatchProcessor()
            processor._update_job_status(job_id, 'processing')
            
            results = []
            processed = 0
            failed = 0
            
            for i, file_info in enumerate(files):
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={'current': i, 'total': len(files), 'status': f'Processing {file_info["original_filename"]}'}
                )
                
                try:
                    result = processor._process_single_email_sync(
                        file_info['stored_path'],
                        file_info['original_filename'],
                        BatchJobConfig(**config)
                    )
                    results.append(result)
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process {file_info['original_filename']}: {e}")
                    failed += 1
                
                # Update database progress
                processor._update_job_progress(job_id, processed, failed)
            
            # Complete the job
            processor._complete_job(job_id, results)
            
            return {'status': 'completed', 'processed': processed, 'failed': failed}
            
        except Exception as e:
            logger.error(f"Batch job {job_id} failed in Celery: {e}")
            processor._update_job_status(job_id, 'failed', str(e))
            raise
    
    @celery_app.task
    def process_single_email(file_path: str, filename: str, config: Dict) -> Dict:
        """Celery task to process a single email"""
        processor = BatchProcessor()
        return processor._process_single_email_sync(file_path, filename, BatchJobConfig(**config))


# Global batch processor instance
_batch_processor = None

def get_batch_processor() -> BatchProcessor:
    """Get global batch processor instance"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor

def reset_batch_processor():
    """Reset global batch processor (mainly for testing)"""
    global _batch_processor
    _batch_processor = None