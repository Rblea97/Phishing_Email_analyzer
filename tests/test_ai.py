"""
Test Suite for AI Integration (Phase 3) - GPT-4o-mini Analysis

Comprehensive tests for AI phishing detection with mocked OpenAI API calls
to prevent actual API usage during testing.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

# Set test environment before importing services
os.environ['OPENAI_API_KEY'] = 'test-key-for-mocking'

from services.ai import (
    AIPhishingAnalyzer, analyze_email_with_ai, get_ai_analyzer,
    AIAnalysisResult, MODEL_NAME, INPUT_TOKEN_LIMIT
)
from services.schema import validate_ai_response, AIResponseValidator
from services.parser import parse_email_content


class TestAIResponseValidator:
    """Test JSON schema validation for AI responses"""
    
    def test_valid_response_validation(self):
        """Test validation of properly formatted AI response"""
        valid_response = {
            "score": 75,
            "label": "Likely Phishing",
            "evidence": [
                {"id": "SPF_FAIL", "description": "SPF authentication failed", "weight": 25},
                {"id": "SUSPICIOUS_URL", "description": "Contains suspicious .xyz domain", "weight": 20}
            ]
        }
        
        is_valid, error, sanitized = validate_ai_response(valid_response)
        
        assert is_valid == True
        assert error is None
        assert sanitized['score'] == 75
        assert sanitized['label'] == "Likely Phishing"
        assert len(sanitized['evidence']) == 2
    
    def test_invalid_score_validation(self):
        """Test validation rejects invalid scores"""
        invalid_response = {
            "score": 150,  # Invalid score > 100
            "label": "Likely Phishing",
            "evidence": []
        }
        
        validator = AIResponseValidator()
        is_valid, error = validator.validate_response(invalid_response)
        
        assert is_valid == False
        assert "150 is greater than the maximum" in error
    
    def test_invalid_label_validation(self):
        """Test validation rejects invalid labels"""
        invalid_response = {
            "score": 50,
            "label": "Invalid Label",
            "evidence": []
        }
        
        validator = AIResponseValidator()
        is_valid, error = validator.validate_response(invalid_response)
        
        assert is_valid == False
        assert "'Invalid Label' is not one of" in error
    
    def test_label_score_consistency_validation(self):
        """Test business logic validation for label-score consistency"""
        # High score should have "Likely Phishing" label
        inconsistent_response = {
            "score": 85,
            "label": "Likely Safe",  # Inconsistent with high score
            "evidence": []
        }
        
        validator = AIResponseValidator()
        is_valid, error = validator.validate_response(inconsistent_response)
        
        assert is_valid == False
        assert "High score should have 'Likely Phishing' label" in error
    
    def test_response_sanitization(self):
        """Test that malformed responses are properly sanitized"""
        malformed_response = {
            "score": "not a number",
            "label": "Invalid Label",
            "evidence": [
                {"id": "INVALID@ID!", "description": "x" * 600, "weight": -10},
                {"id": "", "description": "", "weight": 200}
            ]
        }
        
        validator = AIResponseValidator()
        sanitized = validator.sanitize_response(malformed_response)
        
        # Check sanitization
        assert isinstance(sanitized['score'], int)
        assert 0 <= sanitized['score'] <= 100
        assert sanitized['label'] in ["Likely Safe", "Suspicious", "Likely Phishing"]
        
        # Check evidence sanitization
        for evidence in sanitized['evidence']:
            assert len(evidence['id']) <= 50
            assert len(evidence['description']) <= 500
            assert 1 <= evidence['weight'] <= 100
            # ID should only contain valid characters
            assert all(c.isalnum() or c == '_' for c in evidence['id'])
    
    def test_evidence_weight_validation(self):
        """Test validation of evidence weights vs score"""
        response_with_label_mismatch = {
            "score": 30,
            "label": "Suspicious",
            "evidence": [
                {"id": "RULE_ONE", "description": "Test", "weight": 15},
                {"id": "RULE_TWO", "description": "Test", "weight": 10}
            ]
        }
        
        validator = AIResponseValidator()
        is_valid, error = validator.validate_response(response_with_label_mismatch)
        
        assert is_valid == False
        assert "Low score should have 'Likely Safe' label" in error


class TestAIPhishingAnalyzer:
    """Test the main AI analyzer class with mocked OpenAI calls"""
    
    @pytest.fixture
    def mock_openai_response(self):
        """Fixture providing mock OpenAI API response"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 72,
            "label": "Likely Phishing",
            "evidence": [
                {"id": "AUTH_FAIL", "description": "SPF record failed", "weight": 20},
                {"id": "URL_SUSPICIOUS", "description": "Suspicious .xyz domain", "weight": 15},
                {"id": "URGENCY", "description": "Detected urgent action language", "weight": 10}
            ]
        })
        mock_response.usage.total_tokens = 245
        return mock_response
    
    @pytest.fixture
    def sample_parsed_email(self):
        """Fixture providing a sample parsed email"""
        email_content = b"""From: test@suspicious.xyz
To: victim@example.com
Subject: URGENT: Verify Your Account Now!

Your account will be suspended unless you verify immediately!
Click here: https://fake-bank.xyz/verify
"""
        return parse_email_content(email_content, "test_email.eml")
    
    def test_analyzer_initialization_with_api_key(self):
        """Test analyzer initializes properly with API key"""
        analyzer = AIPhishingAnalyzer(api_key="test-key")
        assert analyzer.api_key == "test-key"
        assert analyzer.client is not None
    
    def test_analyzer_initialization_no_api_key(self):
        """Test analyzer raises error without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                AIPhishingAnalyzer()
    
    @patch('services.ai.OpenAI')
    def test_successful_ai_analysis(self, mock_openai_class, mock_openai_response, sample_parsed_email):
        """Test successful AI analysis with valid response"""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response
        
        # Test analysis
        analyzer = AIPhishingAnalyzer(api_key="test-key")
        result = analyzer.analyze_email(sample_parsed_email)
        
        # Verify results
        assert isinstance(result, AIAnalysisResult)
        assert result.success == True
        assert result.score == 72
        assert result.label == "Likely Phishing"
        assert len(result.evidence) == 3
        assert result.tokens_used == 245
        assert result.cost_estimate > 0
        assert result.processing_time_ms > 0
        
        # Verify API was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == MODEL_NAME
        assert len(call_args[1]['messages']) == 2
        assert call_args[1]['messages'][0]['role'] == 'system'
        assert call_args[1]['messages'][1]['role'] == 'user'
    
    @patch('services.ai.OpenAI')
    def test_api_timeout_handling(self, mock_openai_class, sample_parsed_email):
        """Test handling of API timeout errors"""
        # Setup mock to raise timeout
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Request timed out")
        
        # Test analysis
        analyzer = AIPhishingAnalyzer(api_key="test-key")
        result = analyzer.analyze_email(sample_parsed_email)
        
        # Verify error handling
        assert result.success == False
        assert "Request timed out" in result.error_message
        assert result.score == 50  # Default fallback score
        assert result.label == "Suspicious"  # Default fallback label
        assert result.tokens_used == 0
    
    @patch('services.ai.OpenAI')
    def test_invalid_json_response_handling(self, mock_openai_class, sample_parsed_email):
        """Test handling of invalid JSON response from AI"""
        # Setup mock with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not valid JSON"
        mock_response.usage.total_tokens = 100
        
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test analysis
        analyzer = AIPhishingAnalyzer(api_key="test-key")
        result = analyzer.analyze_email(sample_parsed_email)
        
        # Verify error handling
        assert result.success == False
        assert "Invalid JSON response" in result.error_message
        assert result.score == 50
        assert result.label == "Suspicious"
    
    @patch('services.ai.OpenAI')
    def test_prompt_truncation(self, mock_openai_class, mock_openai_response):
        """Test that oversized prompts are properly truncated"""
        # Create email with very long content
        long_content = "x" * 10000
        email_content = f"""From: test@example.com
To: victim@example.com
Subject: Test

{long_content}
""".encode()
        
        parsed_email = parse_email_content(email_content, "long_email.eml")
        
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response
        
        # Test analysis
        analyzer = AIPhishingAnalyzer(api_key="test-key")
        result = analyzer.analyze_email(parsed_email)
        
        # Verify analysis succeeded and prompt was handled
        assert result.success == True
        
        # Check that the prompt was reasonable length
        call_args = mock_client.chat.completions.create.call_args
        prompt = call_args[1]['messages'][1]['content']
        estimated_tokens = len(prompt) // 4
        assert estimated_tokens <= INPUT_TOKEN_LIMIT
    
    def test_cost_calculation(self):
        """Test cost calculation for token usage"""
        analyzer = AIPhishingAnalyzer(api_key="test-key")
        
        # Test cost calculation
        cost = analyzer._calculate_cost(input_tokens=1000, output_tokens=500)
        
        # Should be: (1000 * 0.000150/1000) + (500 * 0.000600/1000)
        expected_cost = (1000 * 0.000150 / 1000) + (500 * 0.000600 / 1000)
        assert abs(cost - expected_cost) < 0.0001
    
    def test_daily_usage_tracking(self):
        """Test daily usage statistics tracking"""
        analyzer = AIPhishingAnalyzer(api_key="test-key")
        
        # Simulate usage
        analyzer.daily_tokens_used = 1500
        analyzer.daily_cost = 0.025
        
        usage = analyzer.get_daily_usage()
        
        assert usage['tokens_used'] == 1500
        assert usage['cost_estimate'] == 0.025
        
        # Test reset
        analyzer.reset_daily_usage()
        usage_after_reset = analyzer.get_daily_usage()
        
        assert usage_after_reset['tokens_used'] == 0
        assert usage_after_reset['cost_estimate'] == 0
    
    @patch('services.ai.OpenAI')
    def test_retry_mechanism(self, mock_openai_class, mock_openai_response, sample_parsed_email):
        """Test API retry mechanism on failures"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # First call fails, second succeeds
        mock_client.chat.completions.create.side_effect = [
            Exception("Temporary failure"),
            mock_openai_response
        ]
        
        analyzer = AIPhishingAnalyzer(api_key="test-key")
        result = analyzer.analyze_email(sample_parsed_email)
        
        # Should succeed after retry
        assert result.success == True
        assert result.score == 72
        
        # Verify retry happened
        assert mock_client.chat.completions.create.call_count == 2


class TestAIServiceIntegration:
    """Test AI service integration functions"""
    
    @patch('services.ai.get_ai_analyzer')
    def test_analyze_email_with_ai_success(self, mock_get_analyzer):
        """Test successful email analysis via service function"""
        # Setup mock analyzer
        mock_analyzer = Mock()
        mock_result = AIAnalysisResult(
            score=65,
            label="Suspicious",
            evidence=[{"id": "TEST", "description": "Test evidence", "weight": 15}],
            tokens_used=200,
            cost_estimate=0.001,
            processing_time_ms=450.0,
            success=True
        )
        mock_analyzer.analyze_email.return_value = mock_result
        mock_get_analyzer.return_value = mock_analyzer
        
        # Create sample email
        email_content = b"From: test@example.com\nSubject: Test\n\nTest content"
        parsed_email = parse_email_content(email_content, "test.eml")
        
        # Test analysis
        result = analyze_email_with_ai(parsed_email)
        
        assert result.success == True
        assert result.score == 65
        assert result.label == "Suspicious"
        assert result.tokens_used == 200
    
    @patch('services.ai.get_ai_analyzer')
    def test_analyze_email_with_ai_service_error(self, mock_get_analyzer):
        """Test error handling when AI service is unavailable"""
        mock_get_analyzer.side_effect = ValueError("AI service not available")
        
        # Create sample email
        email_content = b"From: test@example.com\nSubject: Test\n\nTest content"
        parsed_email = parse_email_content(email_content, "test.eml")
        
        # Test analysis
        result = analyze_email_with_ai(parsed_email)
        
        assert result.success == False
        assert "AI service not available" in result.error_message
        assert result.score == 50  # Fallback score
        assert result.tokens_used == 0


class TestAISecurityValidation:
    """Test security aspects of AI integration"""
    
    @patch('services.ai.OpenAI')
    def test_no_binary_content_sent_to_ai(self, mock_openai_class):
        """Ensure no binary content is sent to AI API"""
        # Create email with binary attachment (simulated)
        email_content = b"""From: test@example.com
Subject: Test
Content-Type: multipart/mixed; boundary="boundary123"

--boundary123
Content-Type: text/plain

Text content here

--boundary123
Content-Type: application/octet-stream
Content-Transfer-Encoding: base64

YmluYXJ5IGRhdGEgaGVyZQ==

--boundary123--
"""
        
        parsed_email = parse_email_content(email_content, "test.eml")
        
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Create mock response
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = '{"score": 30, "label": "Likely Safe", "evidence": []}'
        mock_openai_response.usage.total_tokens = 100
        
        mock_client.chat.completions.create.return_value = mock_openai_response
        
        # Test analysis
        analyzer = AIPhishingAnalyzer(api_key="test-key")
        result = analyzer.analyze_email(parsed_email)
        
        # Verify analysis succeeded
        assert result.success == True
        
        # Check that prompt contains no binary data
        call_args = mock_client.chat.completions.create.call_args
        prompt = call_args[1]['messages'][1]['content']
        
        # Should not contain base64 or binary indicators
        assert "base64" not in prompt.lower()
        assert "binary" not in prompt.lower()
        assert "YmluYXJ5IGRhdGEgaGVyZQ==" not in prompt
    
    def test_input_sanitization(self):
        """Test that email input is properly sanitized"""
        analyzer = AIPhishingAnalyzer(api_key="test-key")
        
        # Create email with potentially dangerous content
        email_content = b"""From: attacker@evil.com
Subject: <script>alert('xss')</script>
Content-Type: text/plain

This contains potentially dangerous content:
- JavaScript: <script>alert('xss')</script>
- SQL injection attempt: '; DROP TABLE users; --
- Very long line: """ + b"x" * 5000
        
        parsed_email = parse_email_content(email_content, "dangerous.eml")
        prompt = analyzer._create_analysis_prompt(parsed_email)
        
        # Verify content is truncated and safe
        assert len(prompt) < 20000  # Should be truncated
        assert "<script>" in prompt  # But legitimate content preserved for analysis
        
        # Verify truncation works
        truncated = analyzer._truncate_prompt(prompt)
        estimated_tokens = len(truncated) // 4
        assert estimated_tokens <= INPUT_TOKEN_LIMIT
    
    def test_api_key_handling(self):
        """Test secure API key handling"""
        # Test with environment variable
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'env-key'}):
            analyzer = AIPhishingAnalyzer()
            assert analyzer.api_key == 'env-key'
        
        # Test with direct parameter
        analyzer = AIPhishingAnalyzer(api_key="direct-key")
        assert analyzer.api_key == "direct-key"
        
        # Test error when no key available
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                AIPhishingAnalyzer()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])