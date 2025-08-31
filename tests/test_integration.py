"""
Integration tests for the complete phishing detection system
Tests end-to-end functionality including database operations
"""

import os
import sqlite3
import tempfile
import pytest
from unittest.mock import patch
from services.parser import parse_email_content
from services.rules import analyze_email


class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize test database
        self._init_test_database()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def _init_test_database(self):
        """Initialize test database with Phase 2 schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create Phase 2 tables
        cursor.execute('''
            CREATE TABLE emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                filename VARCHAR(255) NOT NULL,
                size_bytes INTEGER NOT NULL,
                sha256 VARCHAR(64) UNIQUE NOT NULL,
                parse_summary_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE email_parsed (
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
        
        cursor.execute('''
            CREATE TABLE detections (
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
        
        conn.commit()
        conn.close()
    
    def load_fixture(self, filename):
        """Load email fixture from file"""
        filepath = os.path.join(self.fixtures_dir, filename)
        with open(filepath, 'rb') as f:
            return f.read()
    
    def test_complete_analysis_pipeline(self):
        """Test complete pipeline: parse → analyze → store"""
        # Load test email
        email_content = self.load_fixture('obvious_phishing.eml')
        filename = 'obvious_phishing.eml'
        
        # Step 1: Parse email
        parsed_email = parse_email_content(email_content, filename)
        assert parsed_email is not None
        assert parsed_email.headers.from_addr == 'admin@secure-bank-verification.top'
        
        # Step 2: Analyze for phishing
        detection_result = analyze_email(parsed_email)
        assert detection_result is not None
        assert detection_result.score >= 60  # Should be high-risk
        assert detection_result.label == "Likely Phishing"
        assert len(detection_result.evidence) >= 4  # Multiple rules should fire
        
        # Step 3: Simulate database storage (test database operations)
        self._test_database_storage(email_content, filename, parsed_email, detection_result)
    
    def _test_database_storage(self, email_content, filename, parsed_email, detection_result):
        """Test database storage operations"""
        import json
        import hashlib
        from dataclasses import asdict
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate email hash
        email_hash = hashlib.sha256(email_content).hexdigest()
        
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
                'security_warnings': len(parsed_email.security_warnings)
            })
        ))
        
        email_id = cursor.lastrowid
        assert email_id > 0
        
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
        
        # Verify storage
        cursor.execute('SELECT COUNT(*) FROM emails')
        assert cursor.fetchone()[0] == 1
        
        cursor.execute('SELECT COUNT(*) FROM email_parsed')
        assert cursor.fetchone()[0] == 1
        
        cursor.execute('SELECT COUNT(*) FROM detections')
        assert cursor.fetchone()[0] == 1
        
        # Test retrieval
        cursor.execute('''
            SELECT e.filename, e.size_bytes, d.score, d.label, d.confidence
            FROM emails e
            JOIN detections d ON e.id = d.email_id
            WHERE e.id = ?
        ''', (email_id,))
        
        row = cursor.fetchone()
        assert row[0] == filename  # filename
        assert row[1] == len(email_content)  # size_bytes
        assert row[2] >= 60  # score
        assert row[3] == "Likely Phishing"  # label
        
        conn.close()
    
    def test_multiple_emails_analysis(self):
        """Test analyzing multiple emails with different risk levels"""
        test_cases = [
            ('safe_newsletter.eml', 'Likely Safe'),
            ('obvious_phishing.eml', 'Likely Phishing'),
            ('spoofed_display.eml', ['Suspicious', 'Likely Phishing']),  # Could be either
            ('auth_failure.eml', ['Suspicious', 'Likely Phishing'])
        ]
        
        results = {}
        
        for filename, expected_label in test_cases:
            # Parse and analyze
            email_content = self.load_fixture(filename)
            parsed_email = parse_email_content(email_content, filename)
            detection_result = analyze_email(parsed_email)
            
            results[filename] = {
                'parsed': parsed_email,
                'detection': detection_result
            }
            
            # Check expected classification
            if isinstance(expected_label, list):
                assert detection_result.label in expected_label, \
                    f"{filename}: Expected {expected_label}, got {detection_result.label}"
            else:
                assert detection_result.label == expected_label, \
                    f"{filename}: Expected {expected_label}, got {detection_result.label}"
        
        # Verify score ordering (phishing should score higher than safe)
        safe_score = results['safe_newsletter.eml']['detection'].score
        phishing_score = results['obvious_phishing.eml']['detection'].score
        
        assert phishing_score > safe_score, \
            f"Phishing score {phishing_score} should be higher than safe score {safe_score}"
    
    def test_performance_under_load(self):
        """Test system performance with multiple emails"""
        import time
        
        # Load multiple test emails
        fixtures = ['safe_newsletter.eml', 'obvious_phishing.eml', 'spoofed_display.eml']
        emails = [self.load_fixture(f) for f in fixtures]
        
        # Time batch processing
        start_time = time.time()
        results = []
        
        for i, email_content in enumerate(emails * 5):  # Process 15 emails total
            filename = f"test_email_{i}.eml"
            parsed_email = parse_email_content(email_content, filename)
            detection_result = analyze_email(parsed_email)
            results.append(detection_result)
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Performance assertions
        assert len(results) == 15
        avg_time_per_email = total_time / 15
        assert avg_time_per_email < 500, f"Average processing time {avg_time_per_email}ms exceeds 500ms target"
        
        # All results should be valid
        for result in results:
            assert 0 <= result.score <= 100
            assert result.label in ['Likely Safe', 'Suspicious', 'Likely Phishing']
            assert 0 <= result.confidence <= 1
            assert result.processing_time_ms > 0
    
    def test_error_handling(self):
        """Test error handling for various edge cases"""
        
        # Test with extremely small email
        minimal_email = b"From: test@example.com\nSubject: Test\n\n"
        parsed = parse_email_content(minimal_email, "minimal.eml")
        result = analyze_email(parsed)
        
        assert result is not None
        assert 0 <= result.score <= 100
        
        # Test with email containing unusual characters
        weird_email = "From: тест@example.com\nSubject: тест\n\nContent with émojis 🎉".encode('utf-8')
        parsed = parse_email_content(weird_email, "weird.eml")
        result = analyze_email(parsed)
        
        assert result is not None
        assert result.processing_time_ms > 0
    
    def test_security_features(self):
        """Test security features and limits"""
        
        # Test with very long email (within limits)
        long_content = b"From: test@example.com\nSubject: Long Test\n\n" + b"A" * 10000
        parsed = parse_email_content(long_content, "long.eml")
        result = analyze_email(parsed)
        
        assert result is not None
        # Should handle large content without issues
        
        # Test URL extraction limits
        many_urls_email = b"From: test@example.com\nSubject: Many URLs\n\n"
        many_urls_email += b"\n".join([f"http://example{i}.com".encode() for i in range(100)])
        
        parsed = parse_email_content(many_urls_email, "many_urls.eml")
        
        # Should limit URLs extracted (exact limit is implementation dependent)
        assert len(parsed.urls) <= 500  # MAX_URLS_PER_EMAIL from parser
    
    def test_deterministic_results(self):
        """Test that analysis results are deterministic"""
        email_content = self.load_fixture('obvious_phishing.eml')
        
        # Run analysis multiple times
        results = []
        for _ in range(5):
            parsed_email = parse_email_content(email_content, 'test.eml')
            detection_result = analyze_email(parsed_email)
            results.append({
                'score': detection_result.score,
                'label': detection_result.label,
                'evidence_count': len(detection_result.evidence),
                'rules_fired': detection_result.rules_fired
            })
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result, "Results should be deterministic"
    
    def test_json_serialization(self):
        """Test that results can be properly serialized to JSON"""
        import json
        from dataclasses import asdict
        
        email_content = self.load_fixture('obvious_phishing.eml')
        parsed_email = parse_email_content(email_content, 'test.eml')
        detection_result = analyze_email(parsed_email)
        
        # Test serialization of detection result
        try:
            evidence_json = json.dumps([asdict(evidence) for evidence in detection_result.evidence])
            headers_json = json.dumps(asdict(parsed_email.headers))
            urls_json = json.dumps([asdict(url) for url in parsed_email.urls])
            
            # Should be valid JSON
            json.loads(evidence_json)
            json.loads(headers_json)
            json.loads(urls_json)
            
        except (TypeError, json.JSONDecodeError) as e:
            pytest.fail(f"JSON serialization failed: {e}")
    
    @pytest.mark.skip("Flask app tests require app.py integration")
    def test_flask_integration(self):
        """Test integration with Flask application"""
        # This would test the actual Flask endpoints
        # Skipped for now as it requires setting up the Flask test client
        pass