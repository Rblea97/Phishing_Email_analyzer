"""
AI-Powered Phishing Email Detection System - Phase 2 MVP
Flask web application with email parsing and rule-based phishing detection
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
import magic

# Import our Phase 2 services
from services.parser import parse_email_content, get_email_hash, EmailParsingError
from services.rules import analyze_email

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB max file size

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'.eml', '.txt', '.msg'}
DATABASE_PATH = os.getenv('DATABASE_PATH', 'phishing_detector.db')

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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
    """Validate file content using magic numbers"""
    try:
        file_start = file.read(1024)
        file.seek(0)
        mime_type = magic.from_buffer(file_start, mime=True)
        
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


def store_email_analysis(email_content, filename, parsed_email, detection_result):
    """Store complete email analysis in database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate unique request ID for logging
        request_id = str(uuid.uuid4())[:8]
        
        # Calculate email hash
        email_hash = get_email_hash(email_content)
        
        # Store in emails table
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
                'request_id': request_id
            })
        ))
        
        email_id = cursor.lastrowid
        
        # Store parsed content
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
        
        # Store detection results
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
        
        conn.commit()
        
        # Log successful analysis (no PII)
        logger.info(f"Analysis complete [{request_id}]: "
                   f"score={detection_result.score}, "
                   f"label={detection_result.label}, "
                   f"evidence_count={len(detection_result.evidence)}, "
                   f"file_size={len(email_content)}")
        
        return email_id
        
    except Exception as e:
        logger.error(f"Database storage error: {str(e)}")
        return None
    finally:
        conn.close()


def get_analysis_by_id(email_id):
    """Retrieve complete analysis by email ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get email info and detection results
        cursor.execute('''
            SELECT e.*, d.score, d.label, d.confidence, d.evidence_json,
                   d.processing_time_ms, d.rules_checked, d.rules_fired,
                   d.created_at as analyzed_at
            FROM emails e
            JOIN detections d ON e.id = d.email_id
            WHERE e.id = ?
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
        
        return {
            'email': dict(row),
            'parsed': dict(parsed_row) if parsed_row else None
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
            JOIN detections d ON e.id = d.email_id
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
            flash('Invalid file type. Please upload .eml, .txt, or .msg files only.', 'error')
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
            flash('Invalid file format. Please upload a valid email file.', 'error')
            return redirect(request.url)
        
        # Parse email with our Phase 2 parser
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
            flash(f'Analysis failed: {str(e)}', 'error')
            logger.error(f"Analysis failed for '{secure_name}': {str(e)}")
            return redirect(request.url)
        
        # Store results in database
        email_id = store_email_analysis(email_content, secure_name, parsed_email, detection_result)
        
        if email_id:
            flash(f'Email analyzed successfully!', 'success')
            return redirect(url_for('view_analysis', email_id=email_id))
        else:
            flash('Error storing analysis results', 'error')
            return redirect(request.url)
    
    except RequestEntityTooLarge:
        flash('File too large. Maximum size allowed is 25MB.', 'error')
        return redirect(request.url)
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        flash('An error occurred during file processing', 'error')
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
    """Display system statistics with Phase 2 data"""
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
        
        return render_template('stats.html', 
                             total_analyses=total_analyses,
                             label_stats=label_stats,
                             score_stats=score_stats,
                             daily_stats=daily_stats)
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        flash('Error retrieving statistics', 'error')
        return redirect(url_for('index'))
    finally:
        conn.close()


@app.route('/health')
def health_check():
    """Enhanced health check for Phase 2"""
    try:
        conn = get_db_connection()
        
        # Test database connectivity
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM emails')
        email_count = cursor.fetchone()[0]
        
        # Check Phase 2 tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        phase2_tables = ['emails', 'email_parsed', 'detections']
        missing_tables = [t for t in phase2_tables if t not in tables]
        
        # Test parser and rule engine
        parser_status = "ok"
        rules_status = "ok"
        
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
        
        health_data = {
            'status': 'healthy' if not missing_tables else 'degraded',
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat(),
            'database': {
                'emails': email_count,
                'missing_tables': missing_tables
            },
            'services': {
                'parser': parser_status,
                'rules': rules_status,
                'rules_count': rules_count
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


@app.errorhandler(413)
def too_large(e):
    """Handle file too large errors"""
    flash('File too large. Maximum size allowed is 25MB.', 'error')
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
    # Check if Phase 2 migration is needed
    if not os.path.exists(DATABASE_PATH):
        print("Database not found. Please run:")
        print("1. python init_db.py")
        print("2. python migrate_to_phase2.py")
        exit(1)
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
        if not cursor.fetchone():
            print("Phase 2 tables not found. Please run:")
            print("python migrate_to_phase2.py")
            exit(1)
        conn.close()
    except Exception as e:
        print(f"Database check failed: {e}")
        exit(1)
    
    # Run application
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    
    print(f"Starting Phase 2 MVP server on port {port}")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)