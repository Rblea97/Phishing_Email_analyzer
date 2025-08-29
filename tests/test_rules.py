"""
Unit tests for rule-based detection engine
"""

import os
import pytest
from services.parser import parse_email_content
from services.rules import (
    RuleEngine, analyze_email, 
    HeaderMismatchRule, ReplyToMismatchRule, AuthFailureRule,
    UrgentLanguageRule, URLShortenerRule, SuspiciousTLDRule,
    UnicodeSpoofRule, NoPersonalizationRule, AttachmentKeywordsRule
)


class TestRuleEngine:
    """Test cases for RuleEngine class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.engine = RuleEngine()
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
    
    def load_and_parse_fixture(self, filename):
        """Load and parse email fixture"""
        filepath = os.path.join(self.fixtures_dir, filename)
        with open(filepath, 'rb') as f:
            email_content = f.read()
        return parse_email_content(email_content, filename)
    
    def test_safe_newsletter_analysis(self):
        """Test analysis of safe newsletter - should score low"""
        parsed_email = self.load_and_parse_fixture('safe_newsletter.eml')
        result = self.engine.analyze_email(parsed_email)
        
        # Should be classified as safe
        assert result.score <= 29  # Likely Safe range
        assert result.label == "Likely Safe"
        assert result.confidence > 0.6
        
        # Should have minimal evidence
        assert len(result.evidence) <= 2  # Maybe generic greeting or minor issues
        assert result.rules_checked > 5   # Should check multiple rules
        
        # Performance check
        assert result.processing_time_ms < 1000  # Should be fast
    
    def test_obvious_phishing_analysis(self):
        """Test analysis of obvious phishing - should score high"""
        parsed_email = self.load_and_parse_fixture('obvious_phishing.eml')
        result = self.engine.analyze_email(parsed_email)
        
        # Should be classified as phishing
        assert result.score >= 60  # Likely Phishing range
        assert result.label == "Likely Phishing"
        assert result.confidence > 0.7
        
        # Should have multiple evidence items
        assert len(result.evidence) >= 4  # Multiple rules should fire
        assert result.rules_fired >= 4
        
        # Check specific rules that should fire
        rule_ids = [ev.rule_id for ev in result.evidence]
        assert "AUTH_FAIL_HINTS" in rule_ids    # SPF/DKIM failures
        assert "URL_SHORTENER" in rule_ids      # bit.ly links
        assert "URGENT_LANGUAGE" in rule_ids    # Urgent language
        assert "SUSPICIOUS_TLDS" in rule_ids    # .top domain
    
    def test_spoofed_display_analysis(self):
        """Test analysis of spoofed display name - should be suspicious"""
        parsed_email = self.load_and_parse_fixture('spoofed_display.eml')
        result = self.engine.analyze_email(parsed_email)
        
        # Should be suspicious or phishing
        assert result.score >= 20  # At least suspicious
        assert result.label in ["Suspicious", "Likely Phishing"]
        
        # Should detect header mismatch
        rule_ids = [ev.rule_id for ev in result.evidence]
        assert "HEADER_MISMATCH" in rule_ids or "REPLYTO_MISMATCH" in rule_ids
    
    def test_auth_failure_analysis(self):
        """Test analysis of email with auth failures"""
        parsed_email = self.load_and_parse_fixture('auth_failure.eml')
        result = self.engine.analyze_email(parsed_email)
        
        # Should be suspicious due to auth failures
        assert result.score >= 20  # Auth failures are significant
        
        # Should detect authentication issues
        rule_ids = [ev.rule_id for ev in result.evidence]
        assert "AUTH_FAIL_HINTS" in rule_ids
    
    def test_unicode_spoof_analysis(self):
        """Test analysis of Unicode spoofing attempt"""
        parsed_email = self.load_and_parse_fixture('unicode_spoof.eml')
        result = self.engine.analyze_email(parsed_email)
        
        # Should detect Unicode spoofing
        rule_ids = [ev.rule_id for ev in result.evidence]
        assert "UNICODE_SPOOF" in rule_ids
        
        # Should be at least suspicious
        assert result.score >= 10  # Unicode spoofing adds points


class TestIndividualRules:
    """Test individual rule implementations"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
    
    def load_and_parse_fixture(self, filename):
        """Load and parse email fixture"""
        filepath = os.path.join(self.fixtures_dir, filename)
        with open(filepath, 'rb') as f:
            email_content = f.read()
        return parse_email_content(email_content, filename)
    
    def test_header_mismatch_rule(self):
        """Test HeaderMismatchRule"""
        rule = HeaderMismatchRule()
        
        # Test with spoofed display name
        parsed_email = self.load_and_parse_fixture('spoofed_display.eml')
        evidence = rule.check(parsed_email)
        
        # Should detect mismatch between "Microsoft Office 365" and fake-service123.com
        assert evidence is not None
        assert evidence.rule_id == "HEADER_MISMATCH"
        assert evidence.weight == 15
    
    def test_reply_to_mismatch_rule(self):
        """Test ReplyToMismatchRule"""
        rule = ReplyToMismatchRule()
        
        # Test with different reply-to domain
        parsed_email = self.load_and_parse_fixture('spoofed_display.eml')
        evidence = rule.check(parsed_email)
        
        # Should detect mismatch
        assert evidence is not None
        assert evidence.rule_id == "REPLYTO_MISMATCH"
        assert evidence.weight == 10
    
    def test_auth_failure_rule(self):
        """Test AuthFailureRule"""
        rule = AuthFailureRule()
        
        # Test with auth failures
        parsed_email = self.load_and_parse_fixture('auth_failure.eml')
        evidence = rule.check(parsed_email)
        
        assert evidence is not None
        assert evidence.rule_id == "AUTH_FAIL_HINTS"
        assert evidence.weight == 20
        assert 'fail' in evidence.details.lower()
    
    def test_urgent_language_rule(self):
        """Test UrgentLanguageRule"""
        rule = UrgentLanguageRule()
        
        # Test with urgent phishing email
        parsed_email = self.load_and_parse_fixture('obvious_phishing.eml')
        evidence = rule.check(parsed_email)
        
        assert evidence is not None
        assert evidence.rule_id == "URGENT_LANGUAGE"
        assert evidence.weight == 10
        
        # Should detect urgent phrases
        details_lower = evidence.details.lower()
        assert any(phrase in details_lower for phrase in [
            'urgent', 'immediate action', 'expires today'
        ])
    
    def test_url_shortener_rule(self):
        """Test URLShortenerRule"""
        rule = URLShortenerRule()
        
        # Test with email containing bit.ly
        parsed_email = self.load_and_parse_fixture('obvious_phishing.eml')
        evidence = rule.check(parsed_email)
        
        assert evidence is not None
        assert evidence.rule_id == "URL_SHORTENER"
        assert evidence.weight == 10
        assert 'bit.ly' in evidence.details
    
    def test_suspicious_tld_rule(self):
        """Test SuspiciousTLDRule"""
        rule = SuspiciousTLDRule()
        
        # Test with .top domain
        parsed_email = self.load_and_parse_fixture('obvious_phishing.eml')
        evidence = rule.check(parsed_email)
        
        assert evidence is not None
        assert evidence.rule_id == "SUSPICIOUS_TLDS"
        assert evidence.weight == 10
        assert '.top' in evidence.details
    
    def test_unicode_spoof_rule(self):
        """Test UnicodeSpoofRule"""
        rule = UnicodeSpoofRule()
        
        # Test with Unicode spoofed domain
        parsed_email = self.load_and_parse_fixture('unicode_spoof.eml')
        evidence = rule.check(parsed_email)
        
        assert evidence is not None
        assert evidence.rule_id == "UNICODE_SPOOF"
        assert evidence.weight == 10
    
    def test_no_personalization_rule(self):
        """Test NoPersonalizationRule"""
        rule = NoPersonalizationRule()
        
        # Test with phishing email (likely has generic greeting)
        parsed_email = self.load_and_parse_fixture('obvious_phishing.eml')
        evidence = rule.check(parsed_email)
        
        # May or may not fire depending on content
        if evidence:
            assert evidence.rule_id == "NO_PERSONALIZATION"
            assert evidence.weight == 5
    
    def test_attachment_keywords_rule(self):
        """Test AttachmentKeywordsRule"""
        rule = AttachmentKeywordsRule()
        
        # Test with invoice email (has payment keywords + URLs)
        parsed_email = self.load_and_parse_fixture('auth_failure.eml')
        evidence = rule.check(parsed_email)
        
        # Should fire if there are URLs and payment keywords
        if len(parsed_email.urls) > 0:
            assert evidence is not None
            assert evidence.rule_id == "ATTACHMENT_KEYWORDS"
            assert evidence.weight == 5
    
    def test_rules_with_safe_email(self):
        """Test that rules don't fire inappropriately on safe emails"""
        parsed_email = self.load_and_parse_fixture('safe_newsletter.eml')
        
        # Most rules should not fire on safe newsletter
        rules = [
            HeaderMismatchRule(),
            ReplyToMismatchRule(), 
            AuthFailureRule(),
            URLShortenerRule(),
            SuspiciousTLDRule(),
            UnicodeSpoofRule()
        ]
        
        fired_rules = 0
        for rule in rules:
            evidence = rule.check(parsed_email)
            if evidence:
                fired_rules += 1
        
        # Very few rules should fire on legitimate email
        assert fired_rules <= 1  # Maybe generic greeting rule


class TestRuleEngineIntegration:
    """Integration tests for the complete rule engine"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
    
    def load_and_parse_fixture(self, filename):
        """Load and parse email fixture"""
        filepath = os.path.join(self.fixtures_dir, filename)
        with open(filepath, 'rb') as f:
            email_content = f.read()
        return parse_email_content(email_content, filename)
    
    def test_score_consistency(self):
        """Test that scores are consistent across runs"""
        parsed_email = self.load_and_parse_fixture('obvious_phishing.eml')
        
        # Run analysis multiple times
        results = []
        for _ in range(3):
            result = analyze_email(parsed_email)
            results.append(result)
        
        # Scores should be identical
        scores = [r.score for r in results]
        assert len(set(scores)) == 1  # All scores the same
        
        # Labels should be identical
        labels = [r.label for r in results]
        assert len(set(labels)) == 1  # All labels the same
    
    def test_scoring_boundaries(self):
        """Test score-to-label mapping boundaries"""
        # We can't easily create emails with exact scores, but we can test the logic
        engine = RuleEngine()
        
        # Test boundary conditions in label calculation
        test_cases = [
            (0, "Likely Safe"),
            (15, "Likely Safe"),
            (29, "Likely Safe"),
            (30, "Suspicious"),
            (45, "Suspicious"),
            (59, "Suspicious"), 
            (60, "Likely Phishing"),
            (85, "Likely Phishing"),
            (100, "Likely Phishing")
        ]
        
        for score, expected_label in test_cases:
            label, confidence = engine._calculate_label_and_confidence(score, 3)
            assert label == expected_label, f"Score {score} should map to {expected_label}, got {label}"
            assert 0 <= confidence <= 1, f"Confidence should be 0-1, got {confidence}"
    
    def test_performance_requirements(self):
        """Test that analysis meets performance requirements"""
        parsed_email = self.load_and_parse_fixture('safe_newsletter.eml')
        result = analyze_email(parsed_email)
        
        # Should complete within 500ms target
        assert result.processing_time_ms < 500, f"Analysis took {result.processing_time_ms}ms (target: <500ms)"
    
    def test_all_fixtures_analysis(self):
        """Test analysis on all fixture files"""
        fixtures = [
            'safe_newsletter.eml',
            'obvious_phishing.eml', 
            'spoofed_display.eml',
            'auth_failure.eml',
            'unicode_spoof.eml'
        ]
        
        expected_outcomes = {
            'safe_newsletter.eml': ("Likely Safe", 0, 29),
            'obvious_phishing.eml': ("Likely Phishing", 60, 100),
            'spoofed_display.eml': ("Suspicious", 20, 80),  # Could be either suspicious or phishing
            'auth_failure.eml': ("Suspicious", 15, 60),     # Auth failures are concerning
            'unicode_spoof.eml': ("Suspicious", 10, 80)     # Unicode spoofing
        }
        
        for fixture in fixtures:
            parsed_email = self.load_and_parse_fixture(fixture)
            result = analyze_email(parsed_email)
            
            expected_label, min_score, max_score = expected_outcomes[fixture]
            
            assert min_score <= result.score <= max_score, \
                f"{fixture}: Score {result.score} not in range [{min_score}, {max_score}]"
            
            # Label might vary for borderline cases, but check reasonableness
            assert result.label in ["Likely Safe", "Suspicious", "Likely Phishing"], \
                f"{fixture}: Invalid label {result.label}"
            
            # Basic sanity checks
            assert result.confidence > 0
            assert result.rules_checked > 0
            assert result.processing_time_ms > 0
            assert len(result.evidence) == result.rules_fired