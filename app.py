"""
AI-Powered Phishing Email Detection System
Flask web application for secure email analysis
"""

import os
import sqlite3
import hashlib
from datetime import datetime
from flask import Flask, request, render_template, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from dotenv import load_dotenv
import magic

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB max file size

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'.eml', '.txt', '.msg'}
DATABASE_PATH = os.getenv('DATABASE_PATH', 'phishing_detector.db')

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_database():
    """Initialize SQLite database with required schema"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
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
    
    # Create email analyses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_analyses (
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
    
    # Create URL analyses cache table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS url_analyses (
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
    
    # Create system metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_metrics (
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
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    if not filename:
        return False
    
    # Get file extension (case insensitive)
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTENSIONS

def validate_file_content(file):
    """Validate file content using magic numbers"""
    try:
        # Read first 1024 bytes for magic number detection
        file_start = file.read(1024)
        file.seek(0)  # Reset file pointer
        
        # Check MIME type
        mime_type = magic.from_buffer(file_start, mime=True)
        
        # Allowed MIME types for email files
        allowed_mime_types = {
            'text/plain',
            'message/rfc822',  # Email format
            'application/octet-stream',  # Generic binary (for .msg files)
            'text/x-mail'  # Alternative email MIME type
        }
        
        return mime_type in allowed_mime_types
        
    except Exception as e:
        app.logger.error(f"File validation error: {str(e)}")
        return False

def calculate_file_hash(file_content):
    """Calculate SHA-256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()

def store_email_metadata(filename, file_size, email_hash):
    """Store email metadata in database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO email_analyses 
            (email_hash, filename, file_size, created_at, classification, risk_score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            email_hash,
            filename,
            file_size,
            datetime.now(),
            'pending',  # Analysis pending
            0  # Default risk score
        ))
        
        conn.commit()
        analysis_id = cursor.lastrowid
        conn.close()
        
        return analysis_id
        
    except Exception as e:
        app.logger.error(f"Database error: {str(e)}")
        return None

@app.route('/')
def index():
    """Main upload form page"""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload with security validation"""
    try:
        # Check if file was submitted
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        # Validate file extension
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload .eml, .txt, or .msg files only.', 'error')
            return redirect(request.url)
        
        # Secure the filename
        original_filename = file.filename
        secure_name = secure_filename(original_filename)
        
        # Additional filename validation
        if len(secure_name) > 255:
            flash('Filename too long', 'error')
            return redirect(request.url)
        
        # Read file content for validation
        file_content = file.read()
        file.seek(0)  # Reset for content validation
        
        # Validate file content
        if not validate_file_content(file):
            flash('Invalid file format. Please upload a valid email file.', 'error')
            return redirect(request.url)
        
        # Calculate file hash
        email_hash = calculate_file_hash(file_content)
        file_size = len(file_content)
        
        # Store metadata in database
        analysis_id = store_email_metadata(secure_name, file_size, email_hash)
        
        if analysis_id:
            # For now, just show success - actual analysis will be added in Phase 2
            flash(f'File "{secure_name}" uploaded successfully! Analysis ID: {analysis_id}', 'success')
            
            # Store basic file info for demo purposes
            file_info = {
                'filename': secure_name,
                'size': f"{file_size / 1024:.1f} KB",
                'hash': email_hash[:16] + "...",
                'analysis_id': analysis_id
            }
            
            return render_template('upload.html', file_info=file_info)
        else:
            flash('Error storing file information', 'error')
            return redirect(request.url)
    
    except RequestEntityTooLarge:
        flash('File too large. Maximum size allowed is 25MB.', 'error')
        return redirect(request.url)
    
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        flash('An error occurred during file upload', 'error')
        return redirect(request.url)

@app.route('/health')
def health_check():
    """Health check endpoint for deployment monitoring"""
    try:
        # Test database connection
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute('SELECT 1')
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/stats')
def stats():
    """Display basic system statistics"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get total analyses count
        cursor.execute('SELECT COUNT(*) FROM email_analyses')
        total_analyses = cursor.fetchone()[0]
        
        # Get analyses by day (last 7 days)
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM email_analyses 
            WHERE created_at >= date('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        ''')
        daily_stats = cursor.fetchall()
        
        conn.close()
        
        return render_template('stats.html', 
                             total_analyses=total_analyses,
                             daily_stats=daily_stats)
        
    except Exception as e:
        app.logger.error(f"Stats error: {str(e)}")
        return "Error retrieving statistics", 500

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
    app.logger.error(f"Internal server error: {str(e)}")
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    # Run in debug mode for development
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)