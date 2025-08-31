"""
AI-Powered Phishing Email Detection System
Flask web application with dual analysis: rule-based detection + GPT-4o-mini AI
"""

import os
import sqlite3
import json
import uuid
import time
import logging
from datetime import datetime
from dataclasses import asdict
from flask import Flask, request, render_template, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from dotenv import load_dotenv
# import magic  # Replaced with mimetypes for Windows compatibility
import mimetypes
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Import core services
from services.parser import parse_email_content, get_email_hash, EmailParsingError
from services.rules import analyze_email

# Import AI services
from services.ai import analyze_email_with_ai, get_ai_analyzer, reset_ai_analyzer

# Import Phase 4 services
from services.url_reputation import get_url_reputation_service
from services.cache_manager import get_cache_manager
from services.batch_processor import get_batch_processor
from services.monitoring import get_performance_monitor
from services.report_export import get_export_service

# Load environment variables (force reload to override any existing env vars)
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug: Show what was loaded
api_key_from_env = os.getenv('OPENAI_API_KEY')
if api_key_from_env:
    logger.info(f"Environment loaded API key ending: {api_key_from_env[-10:]}")
    logger.info(f"Environment loaded API key length: {len(api_key_from_env)}")
else:
    logger.warning("No OPENAI_API_KEY found in environment")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB max file size

# Initialize rate limiter for requests
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per hour"],  # General rate limit
    storage_uri="memory://"
)

# AI service availability
AI_ENABLED = bool(os.getenv('OPENAI_API_KEY'))
if AI_ENABLED:
    logger.info("AI analysis enabled with GPT-4o-mini")
else:
    logger.warning("AI analysis disabled - OPENAI_API_KEY not set")

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'.eml', '.txt', '.msg'}
DATABASE_PATH = os.getenv('DATABASE_PATH', 'phishing_detector.db')

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Phase 4 services
try:
    # Initialize performance monitoring
    performance_monitor = get_performance_monitor()
    performance_monitor.start_background_monitoring()
    logger.info("Phase 4 services initialized successfully")
    
    # Initialize cache manager
    cache_manager = get_cache_manager()
    cache_health = cache_manager.health_check()
    logger.info(f"Cache manager status: {cache_health.get('status', 'unknown')}")
    
    PHASE4_ENABLED = True
    
except Exception as e:
    logger.warning(f"Phase 4 services initialization failed: {e}")
    PHASE4_ENABLED = False


def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    if not filename:
        return False
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTENSIONS


def validate_file_content(file):
    """Validate file content using filename and basic checks"""
    try:
        file_start = file.read(1024)
        file.seek(0)
        
        # Use mimetypes based on filename, fallback to text/plain for email files
        mime_type = mimetypes.guess_type(file.filename)[0]
        if not mime_type or file.filename.endswith(('.eml', '.msg', '.txt')):
            mime_type = 'text/plain'  # Assume email files are text-based
        
        allowed_mime_types = {
            'text/plain',
            'message/rfc822',
            'application/octet-stream',
            'text/x-mail'
        }
        
        return mime_type in allowed_mime_types
        
    except Exception as e:
        logger.error(f"File validation error: {str(e)}")
        return False


def store_email_analysis(email_content, filename, parsed_email, detection_result, ai_result=None, url_analysis=None):
    """Store complete email analysis in database (includes AI results)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate unique request ID for logging
        request_id = str(uuid.uuid4())[:8]
        
        # Calculate email hash
        email_hash = get_email_hash(email_content)
        
        # Check if email already exists
        cursor.execute('SELECT id FROM emails WHERE sha256 = ?', (email_hash,))
        existing_email = cursor.fetchone()
        
        if existing_email:
            # Email already exists, use existing ID
            email_id = existing_email[0]
            logger.info(f"Email with hash {email_hash[:8]} already exists, using existing record (ID: {email_id})")
        else:
            # Store new email in emails table
            cursor.execute('''
                INSERT INTO emails (filename, size_bytes, sha256, parse_summary_json)
                VALUES (?, ?, ?, ?)
            ''', (
                filename,
                len(email_content),
                email_hash,
                json.dumps({
                    'parse_time_ms': parsed_email.parse_time_ms,
                    'url_count': len(parsed_email.urls),
                    'security_warnings': len(parsed_email.security_warnings),
                    'request_id': request_id,
                    'ai_enabled': ai_result is not None
                })
            ))
            
            email_id = cursor.lastrowid
        
        # Store or update parsed content
        if not existing_email:
            # Only insert parsed content for new emails
            cursor.execute('''
                INSERT INTO email_parsed (
                    email_id, headers_json, text_body, html_body, html_as_text,
                    urls_json, parse_time_ms, security_warnings
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_id,
                json.dumps(asdict(parsed_email.headers)),
                parsed_email.text_body,
                parsed_email.html_body,
                parsed_email.html_as_text,
                json.dumps([asdict(url) for url in parsed_email.urls]),
                parsed_email.parse_time_ms,
                json.dumps(parsed_email.security_warnings)
            ))
        
        # Store rule-based detection results
        cursor.execute('''
            INSERT INTO detections (
                email_id, score, label, confidence, evidence_json,
                processing_time_ms, rules_checked, rules_fired
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            email_id,
            detection_result.score,
            detection_result.label,
            detection_result.confidence,
            json.dumps([asdict(evidence) for evidence in detection_result.evidence]),
            detection_result.processing_time_ms,
            detection_result.rules_checked,
            detection_result.rules_fired
        ))
        
        # Store AI detection results if available
        if ai_result:
            cursor.execute('''
                INSERT INTO ai_detections (
                    email_id, score, label, evidence_json, tokens_used,
                    cost_estimate, processing_time_ms, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_id,
                ai_result.score,
                ai_result.label,
                json.dumps(ai_result.evidence),
                ai_result.tokens_used,
                ai_result.cost_estimate,
                ai_result.processing_time_ms,
                ai_result.success,
                ai_result.error_message
            ))
            
            # Update daily usage stats
            cursor.execute('''
                INSERT INTO ai_usage_stats (date, requests_count, tokens_used, total_cost)
                VALUES (DATE('now'), 1, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    requests_count = requests_count + 1,
                    tokens_used = tokens_used + ?,
                    total_cost = total_cost + ?,
                    updated_at = CURRENT_TIMESTAMP
            ''', (ai_result.tokens_used, ai_result.cost_estimate, 
                  ai_result.tokens_used, ai_result.cost_estimate))
        
        # Store URL reputation analysis results if available (Phase 4)
        if url_analysis and PHASE4_ENABLED:
            try:
                # Store individual URL analyses in url_analysis table
                for url, result_data in url_analysis['results'].items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO url_analysis (
                            url_hash, original_url, is_malicious, threat_types, 
                            confidence_score, analysis_source, analysis_details,
                            created_at, expires_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        result_data['url'][:64],  # Use first 64 chars as hash for simplicity
                        result_data['url'],
                        result_data['is_malicious'],
                        json.dumps(result_data['threat_types']),
                        result_data['confidence_score'],
                        result_data['source'],
                        json.dumps(result_data['details'] or {}),
                        result_data['analysis_time'],
                        result_data['analysis_time']  # For now, set same as analysis time
                    ))
                
                # Store URL analysis summary for this email
                url_summary_json = json.dumps(url_analysis)
                
                # Try to add URL analysis summary to existing tables if columns exist
                try:
                    cursor.execute('''
                        UPDATE email_parsed 
                        SET url_analysis_summary = ?
                        WHERE email_id = ?
                    ''', (url_summary_json, email_id))
                except sqlite3.OperationalError:
                    # Column doesn't exist yet, that's okay
                    pass
                    
            except Exception as e:
                logger.warning(f"Failed to store URL analysis results: {e}")
        
        conn.commit()
        
        # Log successful analysis (no PII)
        log_msg = (f"Analysis complete [{request_id}]: "
                   f"rule_score={detection_result.score}, "
                   f"label={detection_result.label}, "
                   f"evidence_count={len(detection_result.evidence)}")
        
        if ai_result:
            log_msg += (f", ai_score={ai_result.score}, "
                       f"ai_tokens={ai_result.tokens_used}, "
                       f"ai_cost=${ai_result.cost_estimate:.4f}, "
                       f"ai_success={ai_result.success}")
        
        if url_analysis:
            summary = url_analysis['summary']
            log_msg += (f", urls_analyzed={summary['total_urls']}, "
                       f"malicious_urls={summary['malicious_urls']}, "
                       f"avg_confidence={summary['average_confidence']}")
        
        logger.info(log_msg)
        
        return email_id
        
    except Exception as e:
        logger.error(f"Database storage error: {str(e)}")
        return None
    finally:
        conn.close()


def get_analysis_by_id(email_id):
    """Retrieve complete analysis by email ID (includes AI results)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get email info and rule-based detection results (most recent analysis)
        cursor.execute('''
            SELECT e.*, d.score, d.label, d.confidence, d.evidence_json,
                   d.processing_time_ms, d.rules_checked, d.rules_fired,
                   d.created_at as analyzed_at
            FROM emails e
            JOIN detections d ON e.id = d.email_id
            WHERE e.id = ?
            ORDER BY d.created_at DESC
            LIMIT 1
        ''', (email_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # Get parsed content
        cursor.execute('''
            SELECT headers_json, text_body, html_as_text, urls_json,
                   parse_time_ms, security_warnings
            FROM email_parsed
            WHERE email_id = ?
        ''', (email_id,))
        
        parsed_row = cursor.fetchone()
        
        # Get AI analysis results if available
        ai_analysis = None
        cursor.execute('''
            SELECT score, label, evidence_json, tokens_used, cost_estimate,
                   processing_time_ms, success, error_message, created_at
            FROM ai_detections
            WHERE email_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (email_id,))
        
        ai_row = cursor.fetchone()
        if ai_row:
            ai_analysis = dict(ai_row)
        
        return {
            'email': dict(row),
            'parsed': dict(parsed_row) if parsed_row else None,
            'ai_analysis': ai_analysis
        }
        
    except Exception as e:
        logger.error(f"Analysis retrieval error: {str(e)}")
        return None
    finally:
        conn.close()


def get_recent_analyses(limit=50):
    """Get recent analyses for listing page"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.id, e.filename, e.size_bytes, e.uploaded_at,
                   d.score, d.label, d.confidence, d.rules_fired
            FROM emails e
            JOIN (
                SELECT email_id, score, label, confidence, rules_fired,
                       ROW_NUMBER() OVER (PARTITION BY email_id ORDER BY created_at DESC) as rn
                FROM detections
            ) d ON e.id = d.email_id AND d.rn = 1
            ORDER BY e.uploaded_at DESC
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
        
    except Exception as e:
        logger.error(f"Recent analyses retrieval error: {str(e)}")
        return []
    finally:
        conn.close()


@app.route('/')
def index():
    """Main upload form page"""
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limit AI requests
def upload_file():
    """Enhanced upload handler with full parsing and analysis"""
    try:
        # Validate file upload
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload email files only: .eml (email export), .txt (plain text), or .msg (Outlook message).', 'error')
            return redirect(request.url)
        
        # Secure filename
        original_filename = file.filename
        secure_name = secure_filename(original_filename)
        
        if len(secure_name) > 255:
            flash('Filename too long', 'error')
            return redirect(request.url)
        
        # Read and validate file content
        email_content = file.read()
        file.seek(0)
        
        if not validate_file_content(file):
            flash('Invalid file format. Please ensure the file contains valid email content with proper headers and structure.', 'error')
            return redirect(request.url)
        
        # Parse email with our parser
        try:
            parsed_email = parse_email_content(email_content, secure_name)
        except EmailParsingError as e:
            flash(f'Email parsing failed: {str(e)}', 'error')
            logger.warning(f"Parsing failed for '{secure_name}': {str(e)}")
            return redirect(request.url)
        
        # Run rule-based detection
        try:
            detection_result = analyze_email(parsed_email)
        except Exception as e:
            flash(f'Rule-based analysis failed: {str(e)}', 'error')
            logger.error(f"Rule analysis failed for '{secure_name}': {str(e)}")
            return redirect(request.url)
        
        # Run AI analysis if enabled
        ai_result = None
        if AI_ENABLED:
            try:
                logger.info(f"Running AI analysis for '{secure_name}'")
                
                # AI analysis is working - debug code removed
                
                ai_result = analyze_email_with_ai(parsed_email)
                
                if not ai_result.success:
                    logger.warning(f"AI analysis failed for '{secure_name}': {ai_result.error_message}")
                    # Continue with rule-based results only
                    
            except Exception as e:
                logger.error(f"AI analysis error for '{secure_name}': {str(e)}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                # Continue with rule-based results only
        else:
            logger.debug("AI analysis skipped - not enabled")
        
        # Run URL reputation analysis if Phase 4 is enabled
        url_analysis = None
        if PHASE4_ENABLED and parsed_email.urls:
            try:
                logger.info(f"Running URL reputation analysis for '{secure_name}' ({len(parsed_email.urls)} URLs)")
                url_service = get_url_reputation_service()
                url_results = url_service.analyze_urls([url.normalized for url in parsed_email.urls[:10]])
                url_analysis = {
                    'results': {url: asdict(result) for url, result in url_results.items()},
                    'summary': url_service.get_reputation_summary(url_results)
                }
                logger.info(f"URL analysis completed: {url_analysis['summary']['malicious_urls']} malicious URLs found")
            except Exception as e:
                logger.error(f"URL reputation analysis failed for '{secure_name}': {e}")
        
        # Record performance metrics if Phase 4 is enabled
        if PHASE4_ENABLED:
            try:
                performance_monitor = get_performance_monitor()
                performance_monitor.record_metric(
                    'email_analysis', 'single_email_processing', 
                    time.time() * 1000, 'milliseconds', 'upload_handler',
                    {'filename': secure_name, 'has_urls': len(parsed_email.urls) > 0}
                )
            except Exception as e:
                logger.debug(f"Performance metric recording failed: {e}")
        
        # Store results in database (rule-based, AI, and URL analysis)
        email_id = store_email_analysis(email_content, secure_name, parsed_email, detection_result, ai_result, url_analysis)
        
        if email_id:
            flash(f'Email analyzed successfully!', 'success')
            return redirect(url_for('view_analysis', email_id=email_id))
        else:
            flash('Error storing analysis results', 'error')
            return redirect(request.url)
    
    except RequestEntityTooLarge:
        flash('File too large. Please upload files smaller than 25MB. Consider using email export features to reduce size.', 'error')
        return redirect(request.url)
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        flash('An error occurred during file processing. Please check that your file is a valid email format and try again.', 'error')
        return redirect(request.url)


@app.route('/analysis/<int:email_id>')
def view_analysis(email_id):
    """Display detailed analysis results"""
    analysis = get_analysis_by_id(email_id)
    
    if not analysis:
        flash('Analysis not found', 'error')
        return redirect(url_for('index'))
    
    # Parse JSON data for display
    try:
        analysis['email']['evidence'] = json.loads(analysis['email']['evidence_json'])
        if analysis['parsed']:
            analysis['parsed']['headers'] = json.loads(analysis['parsed']['headers_json'])
            analysis['parsed']['urls'] = json.loads(analysis['parsed']['urls_json'])
            analysis['parsed']['security_warnings'] = json.loads(analysis['parsed']['security_warnings'])
        
        #  Parse AI results if available
        if analysis.get('ai_analysis'):
            try:
                analysis['ai_analysis']['evidence'] = json.loads(analysis['ai_analysis']['evidence_json'])
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"AI JSON parsing error for analysis {email_id}: {str(e)}")
                analysis['ai_analysis'] = None  # Remove invalid AI data
                
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"JSON parsing error for analysis {email_id}: {str(e)}")
        flash('Error displaying analysis results', 'error')
        return redirect(url_for('index'))
    
    return render_template('analysis.html', analysis=analysis)


@app.route('/analyses')
def list_analyses():
    """Display recent analyses list"""
    analyses = get_recent_analyses(50)
    return render_template('analyses.html', analyses=analyses)


@app.route('/stats')
def stats():
    """Display system statistics with Current AI data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total analyses
        cursor.execute('SELECT COUNT(*) FROM emails')
        total_analyses = cursor.fetchone()[0]
        
        # Get analyses by label
        cursor.execute('''
            SELECT label, COUNT(*) as count
            FROM detections
            GROUP BY label
            ORDER BY count DESC
        ''')
        label_stats = [dict(row) for row in cursor.fetchall()]
        
        # Get average score by label
        cursor.execute('''
            SELECT label, AVG(score) as avg_score, COUNT(*) as count
            FROM detections
            GROUP BY label
        ''')
        score_stats = [dict(row) for row in cursor.fetchall()]
        
        # Get daily stats
        cursor.execute('''
            SELECT DATE(uploaded_at) as date, COUNT(*) as count
            FROM emails 
            WHERE uploaded_at >= date('now', '-7 days')
            GROUP BY DATE(uploaded_at)
            ORDER BY date DESC
        ''')
        daily_stats = [dict(row) for row in cursor.fetchall()]
        
        #  Get AI usage stats
        ai_stats = None
        try:
            cursor.execute('''
                SELECT SUM(requests_count) as total_requests,
                       SUM(tokens_used) as total_tokens,
                       SUM(total_cost) as total_cost,
                       AVG(success_rate) as avg_success_rate
                FROM ai_usage_stats
                WHERE date >= date('now', '-30 days')
            ''')
            ai_row = cursor.fetchone()
            
            if ai_row and ai_row[0]:  # If there are AI stats
                ai_stats = dict(ai_row)
                
                # Get recent daily AI usage
                cursor.execute('''
                    SELECT date, requests_count, tokens_used, total_cost
                    FROM ai_usage_stats
                    WHERE date >= date('now', '-7 days')
                    ORDER BY date DESC
                ''')
                ai_stats['daily'] = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.warning(f"AI stats retrieval error: {e}")
            ai_stats = None
        
        return render_template('stats.html', 
                             total_analyses=total_analyses,
                             label_stats=label_stats,
                             score_stats=score_stats,
                             daily_stats=daily_stats,
                             ai_stats=ai_stats,
                             ai_enabled=AI_ENABLED)
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        flash('Error retrieving statistics', 'error')
        return redirect(url_for('index'))
    finally:
        conn.close()


@app.route('/health')
def health_check():
    """Enhanced health check for Current with AI service status"""
    try:
        conn = get_db_connection()
        
        # Test database connectivity
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM emails')
        email_count = cursor.fetchone()[0]
        
        # Check Current tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        phase3_tables = ['emails', 'email_parsed', 'detections', 'ai_detections', 'ai_usage_stats']
        missing_tables = [t for t in phase3_tables if t not in tables]
        
        # Get AI analysis count
        ai_count = 0
        try:
            cursor.execute('SELECT COUNT(*) FROM ai_detections')
            ai_count = cursor.fetchone()[0]
        except:
            pass
        
        # Test parser and rule engine
        parser_status = "ok"
        rules_status = "ok"
        ai_status = "disabled"
        
        try:
            from services.parser import EmailParser
            from services.rules import RuleEngine
            
            parser = EmailParser()
            engine = RuleEngine()
            rules_count = len(engine.rules)
            
        except Exception as e:
            parser_status = f"error: {str(e)}"
            rules_status = f"error: {str(e)}"
            rules_count = 0
        
        # Test AI service
        if AI_ENABLED:
            try:
                analyzer = get_ai_analyzer()
                usage = analyzer.get_daily_usage()
                ai_status = "ok"
                ai_info = {
                    'status': ai_status,
                    'daily_tokens': usage['tokens_used'],
                    'daily_cost': usage['cost_estimate']
                }
            except Exception as e:
                ai_status = f"error: {str(e)}"
                ai_info = {'status': ai_status}
        else:
            ai_info = {'status': 'disabled', 'reason': 'OPENAI_API_KEY not set'}
        
        health_data = {
            'status': 'healthy' if not missing_tables else 'degraded',
            'version': '3.0.0',
            'timestamp': datetime.now().isoformat(),
            'database': {
                'emails': email_count,
                'ai_analyses': ai_count,
                'missing_tables': missing_tables
            },
            'services': {
                'parser': parser_status,
                'rules': rules_status,
                'rules_count': rules_count,
                'ai': ai_info
            }
        }
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        
        return jsonify(health_data), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503
    
    finally:
        conn.close()


# ==================== Phase 4 Routes ====================

@app.route('/api/batch', methods=['POST'])
@limiter.limit("5 per minute")  # More restrictive for batch operations
def create_batch_job():
    """Create new batch processing job"""
    if not PHASE4_ENABLED:
        return jsonify({'error': 'Phase 4 features not available'}), 503
        
    try:
        batch_processor = get_batch_processor()
        
        # Handle file uploads
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files provided'}), 400
            
        # Prepare email files
        email_files = []
        for file in files:
            if file.filename and allowed_file(file.filename):
                content = file.read()
                if len(content) > 0:
                    email_files.append((file.filename, content))
        
        if not email_files:
            return jsonify({'error': 'No valid email files found'}), 400
            
        # Create batch job
        from services.batch_processor import BatchJobConfig
        config = BatchJobConfig(
            enable_ai_analysis=request.form.get('enable_ai', 'true').lower() == 'true',
            enable_url_reputation=request.form.get('enable_url', 'true').lower() == 'true'
        )
        
        job_id = batch_processor.create_batch_job(email_files, config)
        
        return jsonify({
            'job_id': job_id,
            'status': 'created',
            'total_files': len(email_files)
        })
        
    except Exception as e:
        logger.error(f"Batch job creation failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch/<job_id>')
def get_batch_status(job_id):
    """Get batch job status"""
    if not PHASE4_ENABLED:
        return jsonify({'error': 'Phase 4 features not available'}), 503
        
    try:
        batch_processor = get_batch_processor()
        status = batch_processor.get_job_status(job_id)
        
        if not status:
            return jsonify({'error': 'Job not found'}), 404
            
        return jsonify(asdict(status))
        
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch/<job_id>/results')
def get_batch_results(job_id):
    """Get batch job results"""
    if not PHASE4_ENABLED:
        return jsonify({'error': 'Phase 4 features not available'}), 503
        
    try:
        batch_processor = get_batch_processor()
        results = batch_processor.get_job_results(job_id)
        
        if results is None:
            return jsonify({'error': 'Results not found'}), 404
            
        return jsonify({'job_id': job_id, 'results': results})
        
    except Exception as e:
        logger.error(f"Failed to get batch results: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def create_export_request():
    """Create export request for reports"""
    if not PHASE4_ENABLED:
        return jsonify({'error': 'Phase 4 features not available'}), 503
        
    try:
        export_service = get_export_service()
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No request data provided'}), 400
            
        export_type = data.get('export_type', 'json')
        data_type = data.get('data_type', 'single_analysis')  
        reference_id = data.get('reference_id')
        settings = data.get('settings', {})
        
        if not reference_id:
            return jsonify({'error': 'reference_id is required'}), 400
            
        request_id = export_service.create_export_request(
            export_type, data_type, reference_id, settings
        )
        
        # Process the export synchronously for now
        result = export_service.process_export_request(request_id)
        
        return jsonify({
            'request_id': request_id,
            'status': result.status,
            'file_path': result.file_path if result.status == 'completed' else None,
            'error_message': result.error_message
        })
        
    except Exception as e:
        logger.error(f"Export request failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance')
def get_performance_metrics():
    """Get system performance metrics"""
    if not PHASE4_ENABLED:
        return jsonify({'error': 'Phase 4 features not available'}), 503
        
    try:
        performance_monitor = get_performance_monitor()
        
        hours = request.args.get('hours', 24, type=int)
        summary = performance_monitor.get_performance_summary(hours)
        
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance/health')
def get_system_health():
    """Get detailed system health status"""
    if not PHASE4_ENABLED:
        return jsonify({'error': 'Phase 4 features not available'}), 503
        
    try:
        performance_monitor = get_performance_monitor()
        health = performance_monitor.collect_system_metrics()
        
        return jsonify(asdict(health))
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/stats')  
def get_cache_stats():
    """Get cache performance statistics"""
    if not PHASE4_ENABLED:
        return jsonify({'error': 'Phase 4 features not available'}), 503
        
    try:
        cache_manager = get_cache_manager()
        stats = cache_manager.get_stats()
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/url-reputation', methods=['POST'])
def analyze_urls():
    """Analyze URLs for reputation"""
    if not PHASE4_ENABLED:
        return jsonify({'error': 'Phase 4 features not available'}), 503
        
    try:
        data = request.get_json()
        if not data or 'urls' not in data:
            return jsonify({'error': 'URLs required'}), 400
            
        urls = data['urls']
        if not isinstance(urls, list) or len(urls) == 0:
            return jsonify({'error': 'Valid URL list required'}), 400
            
        url_service = get_url_reputation_service()
        results = url_service.analyze_urls(urls[:10])  # Limit to 10 URLs
        
        # Convert results to serializable format
        serializable_results = {}
        for url, result in results.items():
            serializable_results[url] = asdict(result)
            
        summary = url_service.get_reputation_summary(results)
        
        return jsonify({
            'results': serializable_results,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"URL reputation analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(413)
def too_large(e):
    """Handle file too large errors"""
    flash('File too large. Maximum size allowed is 25MB.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    flash('Too many requests. Please wait before analyzing another email.', 'warning')
    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(e)}")
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500


if __name__ == '__main__':
    # Check if Current migration is needed
    if not os.path.exists(DATABASE_PATH):
        print("Database not found. Please run:")
        print("1. python init_db.py")
        print("2. python migrate_to_phase2.py")
        print("3. python migrate_to_phase3.py")
        exit(1)
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check Current tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
        if not cursor.fetchone():
            print("Current tables not found. Please run:")
            print("python migrate_to_phase2.py")
            exit(1)
        
        # Check Current tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_detections'")
        if not cursor.fetchone():
            print("Current tables not found. Please run:")
            print("python migrate_to_phase3.py")
            exit(1)
            
        conn.close()
    except Exception as e:
        print(f"Database check failed: {e}")
        exit(1)
    
    # Check AI configuration
    if AI_ENABLED:
        print("SUCCESS: AI analysis enabled with GPT-4o-mini")
        try:
            # Reset any cached analyzer instance to ensure fresh API key
            reset_ai_analyzer()
            analyzer = get_ai_analyzer()
            print("SUCCESS: OpenAI API key configured")
        except Exception as e:
            print(f"WARNING: AI service warning: {e}")
            print("  AI analysis will be unavailable")
    else:
        print("INFO: AI analysis disabled - set OPENAI_API_KEY to enable")
    
    # Run application
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    
    print(f"Starting Current (AI Integration) server on port {port}")
    print("Rate limits: 10 AI analyses per minute per IP")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)