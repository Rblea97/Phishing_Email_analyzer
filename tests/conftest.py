"""
Pytest configuration and shared fixtures for the test suite
"""

import os
import sys
import pytest

# Add the project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Test configuration
pytest_plugins = []


@pytest.fixture(scope="session")
def fixtures_dir():
    """Provide path to test fixtures directory"""
    return os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture(scope="session")
def sample_emails(fixtures_dir):
    """Load all sample email fixtures"""
    emails = {}
    fixture_files = [
        'safe_newsletter.eml',
        'obvious_phishing.eml',
        'spoofed_display.eml',
        'auth_failure.eml',
        'unicode_spoof.eml'
    ]
    
    for filename in fixture_files:
        filepath = os.path.join(fixtures_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                emails[filename] = f.read()
    
    return emails


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    import tempfile
    import sqlite3
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_file.close()
    
    # Initialize with Phase 2 schema
    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()
    
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
    
    yield temp_file.name
    
    # Cleanup
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark performance tests
        if "performance" in item.name.lower():
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)


# Custom assertions for email analysis
class EmailAnalysisAssertions:
    """Custom assertions for email analysis results"""
    
    @staticmethod
    def assert_valid_detection_result(result):
        """Assert that detection result has valid structure"""
        assert hasattr(result, 'score')
        assert hasattr(result, 'label')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'evidence')
        assert hasattr(result, 'processing_time_ms')
        assert hasattr(result, 'rules_checked')
        assert hasattr(result, 'rules_fired')
        
        # Value validations
        assert 0 <= result.score <= 100
        assert result.label in ['Likely Safe', 'Suspicious', 'Likely Phishing']
        assert 0 <= result.confidence <= 1
        assert isinstance(result.evidence, list)
        assert result.processing_time_ms > 0
        assert result.rules_checked > 0
        assert result.rules_fired >= 0
        assert result.rules_fired <= result.rules_checked
        assert len(result.evidence) == result.rules_fired
    
    @staticmethod
    def assert_valid_parsed_email(parsed):
        """Assert that parsed email has valid structure"""
        assert hasattr(parsed, 'headers')
        assert hasattr(parsed, 'text_body')
        assert hasattr(parsed, 'html_body')
        assert hasattr(parsed, 'html_as_text')
        assert hasattr(parsed, 'urls')
        assert hasattr(parsed, 'parse_time_ms')
        assert hasattr(parsed, 'security_warnings')
        assert hasattr(parsed, 'raw_size')
        assert hasattr(parsed, 'parsed_size')
        
        # Type validations
        assert isinstance(parsed.text_body, str)
        assert isinstance(parsed.html_body, str)
        assert isinstance(parsed.html_as_text, str)
        assert isinstance(parsed.urls, list)
        assert isinstance(parsed.security_warnings, list)
        assert parsed.parse_time_ms > 0
        assert parsed.raw_size > 0


@pytest.fixture
def email_assertions():
    """Provide custom email analysis assertions"""
    return EmailAnalysisAssertions()