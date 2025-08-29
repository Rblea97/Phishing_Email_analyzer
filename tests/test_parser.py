"""
Unit tests for email parser module
"""

import os
import pytest
from services.parser import parse_email_content, EmailParser, EmailParsingError


class TestEmailParser:
    """Test cases for EmailParser class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.parser = EmailParser()
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
    
    def load_fixture(self, filename):
        """Load email fixture from file"""
        filepath = os.path.join(self.fixtures_dir, filename)
        with open(filepath, 'rb') as f:
            return f.read()
    
    def test_parse_safe_newsletter(self):
        """Test parsing of safe newsletter email"""
        email_content = self.load_fixture('safe_newsletter.eml')
        parsed = parse_email_content(email_content, 'safe_newsletter.eml')
        
        # Basic structure tests
        assert parsed is not None
        assert parsed.raw_size > 0
        assert parsed.parse_time_ms > 0
        
        # Header tests
        assert parsed.headers.from_addr == 'newsletter@example-company.com'
        assert parsed.headers.from_display == 'Example Company Newsletter'
        assert parsed.headers.to_addr == 'user@example.com'
        assert parsed.headers.subject == 'Weekly Tech Updates - New Product Features'
        assert 'spf=pass' in parsed.headers.authentication_results.lower()
        
        # Content tests
        assert 'Hello John' in parsed.text_body
        assert 'NEW FEATURES' in parsed.text_body
        assert len(parsed.html_as_text) > 0
        
        # URL tests
        assert len(parsed.urls) >= 2  # Should find website and unsubscribe links
        domains = [url.domain for url in parsed.urls]
        assert 'www.example-company.com' in domains
        
        # Security tests
        assert len(parsed.security_warnings) == 0  # Should be clean
    
    def test_parse_obvious_phishing(self):
        """Test parsing of obvious phishing email"""
        email_content = self.load_fixture('obvious_phishing.eml')
        parsed = parse_email_content(email_content, 'obvious_phishing.eml')
        
        # Header tests
        assert parsed.headers.from_addr == 'admin@secure-bank-verification.top'
        assert parsed.headers.from_display == 'Bank of America Security Team'
        assert parsed.headers.reply_to == 'verify-account@temp-verification.click'
        assert 'spf=fail' in parsed.headers.authentication_results.lower()
        
        # Content tests
        assert 'URGENT' in parsed.text_body or 'URGENT' in parsed.html_as_text
        assert 'immediate action' in parsed.html_as_text.lower()
        assert 'expires today' in parsed.html_as_text.lower()
        
        # URL tests
        assert len(parsed.urls) >= 3  # Should find multiple suspicious URLs
        domains = [url.domain for url in parsed.urls]
        assert 'bit.ly' in domains  # URL shortener
        assert any('.top' in domain for domain in domains)  # Suspicious TLD
    
    def test_parse_spoofed_display(self):
        """Test parsing of email with spoofed display name"""
        email_content = self.load_fixture('spoofed_display.eml')
        parsed = parse_email_content(email_content, 'spoofed_display.eml')
        
        # Header mismatch test
        assert parsed.headers.from_display == 'Microsoft Office 365'
        assert parsed.headers.from_addr == 'notifications@fake-service123.com'
        assert parsed.headers.reply_to == 'support@different-domain.net'
        
        # Should detect domain mismatch
        from_domain = parsed.headers.from_addr.split('@')[1] if '@' in parsed.headers.from_addr else ''
        reply_domain = parsed.headers.reply_to.split('@')[1] if '@' in parsed.headers.reply_to else ''
        assert from_domain != reply_domain
    
    def test_parse_auth_failure(self):
        """Test parsing of email with authentication failures"""
        email_content = self.load_fixture('auth_failure.eml')
        parsed = parse_email_content(email_content, 'auth_failure.eml')
        
        # Authentication results should show failures
        auth_results = parsed.headers.authentication_results.lower()
        assert 'softfail' in auth_results or 'fail' in auth_results
        assert 'dkim=fail' in auth_results
        assert 'dmarc=fail' in auth_results
        
        # Content should be business-like but suspicious due to auth failures
        assert 'invoice' in parsed.text_body.lower()
        assert 'payment' in parsed.text_body.lower()
    
    def test_parse_unicode_spoof(self):
        """Test parsing of email with Unicode spoofing"""
        email_content = self.load_fixture('unicode_spoof.eml')
        parsed = parse_email_content(email_content, 'unicode_spoof.eml')
        
        # Should detect suspicious domain
        assert parsed.headers.from_addr == 'security@аррӏе.com'  # Cyrillic characters
        
        # URL tests for Unicode domains
        urls_found = [url.original for url in parsed.urls]
        assert any('аррӏе.com' in url for url in urls_found)
        
        # Should detect non-ASCII characters in domain
        domains = [url.domain for url in parsed.urls]
        has_non_ascii = any(not domain.isascii() for domain in domains)
        assert has_non_ascii or any('xn--' in domain for domain in domains)  # Punycode
    
    def test_url_extraction(self):
        """Test URL extraction and normalization"""
        email_content = self.load_fixture('obvious_phishing.eml')
        parsed = parse_email_content(email_content, 'obvious_phishing.eml')
        
        # Should extract multiple URLs
        assert len(parsed.urls) > 0
        
        # Test URL properties
        for url in parsed.urls:
            assert hasattr(url, 'original')
            assert hasattr(url, 'normalized')
            assert hasattr(url, 'domain')
            assert hasattr(url, 'path')
            assert hasattr(url, 'context')
            
            # Domain should be lowercase
            assert url.domain.islower()
            
            # Should have context around the URL
            assert len(url.context) > 0
    
    def test_html_to_text_conversion(self):
        """Test HTML to text conversion"""
        email_content = self.load_fixture('safe_newsletter.eml')
        parsed = parse_email_content(email_content, 'safe_newsletter.eml')
        
        # Should have both HTML and text versions
        assert len(parsed.html_body) > 0
        assert len(parsed.html_as_text) > 0
        
        # HTML should be stripped in text version
        assert '<html>' not in parsed.html_as_text
        assert '<body>' not in parsed.html_as_text
        
        # Content should be preserved
        assert 'Hello John' in parsed.html_as_text
    
    def test_security_limits(self):
        """Test security limits and validation"""
        # Test with very large fake email
        large_content = b"From: test@example.com\nSubject: Test\n\n" + b"A" * (2 * 1024 * 1024)  # 2MB
        
        # Should not raise exception but may truncate
        parsed = parse_email_content(large_content, 'large_test.eml')
        assert parsed is not None
        
        # May have security warnings about truncation
        # (Implementation should handle large files gracefully)
    
    def test_malformed_email_handling(self):
        """Test handling of malformed email content"""
        # Test with invalid MIME structure
        malformed_content = b"This is not a valid email\nNo headers\nJust random content"
        
        # Should either parse gracefully or raise EmailParsingError
        try:
            parsed = parse_email_content(malformed_content, 'malformed.eml')
            # If it parses, should have minimal structure
            assert parsed is not None
        except EmailParsingError:
            # This is also acceptable for malformed content
            pass
    
    def test_empty_email_handling(self):
        """Test handling of empty or minimal email content"""
        minimal_content = b"From: test@example.com\nTo: user@example.com\nSubject: Test\n\n"
        
        parsed = parse_email_content(minimal_content, 'minimal.eml')
        assert parsed is not None
        assert parsed.headers.from_addr == 'test@example.com'
        assert parsed.headers.to_addr == 'user@example.com'
        assert parsed.headers.subject == 'Test'
    
    def test_performance_timing(self):
        """Test that parsing completes within reasonable time"""
        email_content = self.load_fixture('safe_newsletter.eml')
        parsed = parse_email_content(email_content, 'safe_newsletter.eml')
        
        # Should complete parsing in reasonable time (adjust threshold as needed)
        assert parsed.parse_time_ms < 5000  # 5 seconds max for test emails
        assert parsed.parse_time_ms > 0     # Should take some time
    
    def test_character_encoding_handling(self):
        """Test handling of various character encodings"""
        # Test files should contain various encodings
        for fixture in ['safe_newsletter.eml', 'unicode_spoof.eml']:
            email_content = self.load_fixture(fixture)
            parsed = parse_email_content(email_content, fixture)
            
            # Should handle encoding without crashing
            assert parsed is not None
            assert len(parsed.headers.subject) > 0
            
            # Text should be readable Unicode
            assert isinstance(parsed.text_body, str)
            assert isinstance(parsed.html_as_text, str)