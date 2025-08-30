"""
AI-Powered Phishing Detection Service - Phase 3 GPT-4o-mini Integration

Provides structured phishing analysis using OpenAI GPT-4o-mini with comprehensive
security controls, cost monitoring, and response validation.
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from openai import OpenAI

from .parser import ParsedEmail
from .schema import validate_ai_response

logger = logging.getLogger(__name__)

# GPT-4o-mini model configuration
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS = 1000  # Response tokens
INPUT_TOKEN_LIMIT = 4000  # Input tokens
TIMEOUT_SECONDS = 10
MAX_RETRIES = 2

# Cost calculation (approximate rates for GPT-4o-mini)
COST_PER_INPUT_TOKEN = 0.000150 / 1000  # $0.15 per 1M tokens
COST_PER_OUTPUT_TOKEN = 0.000600 / 1000  # $0.60 per 1M tokens


@dataclass
class AIAnalysisResult:
    """Result of AI phishing analysis"""

    score: int
    label: str
    evidence: list
    tokens_used: int
    cost_estimate: float
    processing_time_ms: float
    success: bool
    error_message: Optional[str] = None


class AIPhishingAnalyzer:
    """OpenAI GPT-4o-mini powered phishing detection"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI analyzer

        Args:
            api_key: OpenAI API key (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        # Debug logging for API key
        logger.info(f"AI Analyzer initialized with API key ending: {self.api_key[-10:]}")

        self.client = OpenAI(api_key=self.api_key)
        self.daily_tokens_used = 0
        self.daily_cost = 0.0

    def _create_analysis_prompt(self, parsed_email: ParsedEmail) -> str:
        """
        Create structured prompt for GPT-4o-mini analysis

        Args:
            parsed_email: Parsed email data

        Returns:
            Formatted prompt string
        """
        # Sanitize and truncate email content
        subject = (
            parsed_email.headers.subject[:200] if parsed_email.headers.subject else "No subject"
        )
        sender = (
            parsed_email.headers.from_addr[:100]
            if parsed_email.headers.from_addr
            else "Unknown sender"
        )
        body_text = parsed_email.text_body[:2000] if parsed_email.text_body else ""

        # Extract key headers for analysis
        headers_info = []
        if parsed_email.headers:
            # Key headers to include in analysis
            key_headers = {
                "from_addr": parsed_email.headers.from_addr,
                "from_display": parsed_email.headers.from_display,
                "reply_to": parsed_email.headers.reply_to,
                "return_path": parsed_email.headers.return_path,
                "authentication_results": parsed_email.headers.authentication_results,
            }
            for header, value in key_headers.items():
                if value:
                    headers_info.append(f"{header}: {str(value)[:200]}")

        # URL information
        url_info = []
        if parsed_email.urls:
            for url in parsed_email.urls[:10]:  # Limit to first 10 URLs
                url_info.append(f"URL: {url.normalized}, Domain: {url.domain}")

        prompt = f"""You are a cybersecurity analyst. Analyze this email step-by-step for phishing \
indicators:

EMAIL DETAILS:
Subject: {subject}
Sender: {sender}

HEADERS:
{chr(10).join(headers_info[:10]) if headers_info else "No authentication headers available"}

BODY TEXT (truncated):
{body_text}

URLS FOUND:
{chr(10).join(url_info) if url_info else "No URLs found"}

ANALYSIS INSTRUCTIONS:
1. Examine sender authentication (SPF, DKIM, DMARC status)
2. Identify manipulation tactics in the content
3. Check URLs for suspicious domains or patterns
4. Evaluate for phishing indicators (urgency, generic greetings, etc.)
5. Consider header inconsistencies and spoofing attempts

Return ONLY a JSON object with this exact structure:
{{
  "score": <integer 0-100>,
  "label": "Likely Safe" | "Suspicious" | "Likely Phishing",
  "evidence": [
    {{"id": "RULE_ID", "description": "Brief explanation", "weight": <integer 1-100>}}
  ]
}}

SCORING GUIDELINES:
- 0-30: Likely Safe (legitimate email with minor issues)
- 31-69: Suspicious (mixed signals, proceed with caution)
- 70-100: Likely Phishing (strong indicators of malicious intent)

Evidence IDs should be uppercase with underscores (e.g., SPF_FAIL, SUSPICIOUS_URL)."""

        return prompt

    def _truncate_prompt(self, prompt: str) -> str:
        """
        Truncate prompt to stay within token limits

        Args:
            prompt: Full prompt string

        Returns:
            Truncated prompt
        """
        # Rough estimation: 1 token ≈ 4 characters
        estimated_tokens = len(prompt) // 4

        if estimated_tokens <= INPUT_TOKEN_LIMIT:
            return prompt

        # Truncate from the middle (body text section)
        lines = prompt.split("\n")
        truncated_lines = []
        total_chars = 0
        target_chars = INPUT_TOKEN_LIMIT * 4

        # Keep beginning and end of prompt, truncate middle
        beginning = lines[:15]  # Email details and headers
        ending = lines[-10:]  # Analysis instructions

        for line in beginning + ending:
            if total_chars + len(line) + 1 < target_chars:
                truncated_lines.append(line)
                total_chars += len(line) + 1
            else:
                if "BODY TEXT" in line:
                    truncated_lines.append("BODY TEXT (truncated due to length limits):")
                    truncated_lines.append("[Content truncated for security]")
                break

        logger.info(
            f"Prompt truncated from {len(prompt)} to {len(''.join(truncated_lines))} characters"
        )
        return "\n".join(truncated_lines)

    def _make_api_request(self, prompt: str) -> Tuple[Optional[Dict], int, Optional[str]]:
        """
        Make API request to OpenAI with retries

        Args:
            prompt: Analysis prompt

        Returns:
            tuple: (response_data, tokens_used, error_message)
        """
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a cybersecurity expert specializing in phishing detection. Respond only with valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=MAX_TOKENS,
                    temperature=0.1,  # Low temperature for consistent analysis
                    timeout=TIMEOUT_SECONDS,
                )

                # Extract response content
                content = response.choices[0].message.content.strip()
                tokens_used = response.usage.total_tokens

                # Parse JSON response
                try:
                    response_data = json.loads(content)
                    return response_data, tokens_used, None
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response (attempt {attempt + 1}): {e}")
                    if attempt < MAX_RETRIES:
                        continue
                    return None, 0, f"Invalid JSON response: {str(e)}"

            except Exception as e:
                logger.warning(f"API request failed (attempt {attempt + 1}): {str(e)}")
                if attempt < MAX_RETRIES:
                    time.sleep(1)  # Brief pause before retry
                    continue
                return None, 0, f"API request failed: {str(e)}"

        return None, 0, "Max retries exceeded"

    def analyze_email(self, parsed_email: ParsedEmail) -> AIAnalysisResult:
        """
        Analyze email for phishing using GPT-4o-mini

        Args:
            parsed_email: Parsed email data

        Returns:
            AIAnalysisResult with analysis results
        """
        start_time = time.time()

        try:
            # Create and truncate prompt
            prompt = self._create_analysis_prompt(parsed_email)
            prompt = self._truncate_prompt(prompt)

            # Make API request
            response_data, tokens_used, error = self._make_api_request(prompt)

            if error or not response_data:
                return AIAnalysisResult(
                    score=50,
                    label="Suspicious",
                    evidence=[
                        {
                            "id": "AI_ERROR",
                            "description": error or "Analysis failed",
                            "weight": 10,
                        }
                    ],
                    tokens_used=0,
                    cost_estimate=0.0,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    success=False,
                    error_message=error,
                )

            # Validate and sanitize response
            is_valid, validation_error, sanitized_data = validate_ai_response(response_data)

            if not is_valid:
                logger.warning(f"AI response validation failed: {validation_error}")
                return AIAnalysisResult(
                    score=50,
                    label="Suspicious",
                    evidence=[
                        {
                            "id": "VALIDATION_ERROR",
                            "description": f"Response validation failed: {validation_error}",
                            "weight": 10,
                        }
                    ],
                    tokens_used=tokens_used,
                    cost_estimate=self._calculate_cost(tokens_used, MAX_TOKENS),
                    processing_time_ms=(time.time() - start_time) * 1000,
                    success=False,
                    error_message=validation_error,
                )

            # Calculate cost
            cost = self._calculate_cost(tokens_used, len(sanitized_data.get("evidence", [])) * 50)

            # Update daily tracking
            self.daily_tokens_used += tokens_used
            self.daily_cost += cost

            processing_time = (time.time() - start_time) * 1000

            logger.info(
                f"AI analysis completed: score={sanitized_data['score']}, "
                f"tokens={tokens_used}, cost=${cost:.4f}, time={processing_time:.1f}ms"
            )

            return AIAnalysisResult(
                score=sanitized_data["score"],
                label=sanitized_data["label"],
                evidence=sanitized_data["evidence"],
                tokens_used=tokens_used,
                cost_estimate=cost,
                processing_time_ms=processing_time,
                success=True,
            )

        except Exception as e:
            logger.error(f"Unexpected error in AI analysis: {str(e)}")
            return AIAnalysisResult(
                score=50,
                label="Suspicious",
                evidence=[
                    {
                        "id": "SYSTEM_ERROR",
                        "description": f"System error: {str(e)}",
                        "weight": 10,
                    }
                ],
                tokens_used=0,
                cost_estimate=0.0,
                processing_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message=str(e),
            )

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate estimated cost for API request

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        input_cost = input_tokens * COST_PER_INPUT_TOKEN
        output_cost = output_tokens * COST_PER_OUTPUT_TOKEN
        return input_cost + output_cost

    def get_daily_usage(self) -> Dict[str, Any]:
        """
        Get daily usage statistics

        Returns:
            Dictionary with usage stats
        """
        return {
            "tokens_used": self.daily_tokens_used,
            "cost_estimate": self.daily_cost,
            "requests_made": "Not tracked in current implementation",
        }

    def reset_daily_usage(self):
        """Reset daily usage counters"""
        self.daily_tokens_used = 0
        self.daily_cost = 0.0


# Global analyzer instance (initialized when needed)
_analyzer_instance = None


def reset_ai_analyzer():
    """Reset the global analyzer instance (useful for testing or API key changes)"""
    global _analyzer_instance
    _analyzer_instance = None


def get_ai_analyzer() -> AIPhishingAnalyzer:
    """
    Get global AI analyzer instance

    Returns:
        AIPhishingAnalyzer instance
    """
    global _analyzer_instance
    if _analyzer_instance is None:
        try:
            _analyzer_instance = AIPhishingAnalyzer()
        except ValueError as e:
            logger.error(f"Failed to initialize AI analyzer: {e}")
            raise
    return _analyzer_instance


def analyze_email_with_ai(parsed_email: ParsedEmail) -> AIAnalysisResult:
    """
    Convenience function for AI analysis

    Args:
        parsed_email: Parsed email data

    Returns:
        AIAnalysisResult
    """
    try:
        analyzer = get_ai_analyzer()
        return analyzer.analyze_email(parsed_email)
    except Exception as e:
        logger.error(f"Failed to get AI analyzer: {e}")
        return AIAnalysisResult(
            score=50,
            label="Suspicious",
            evidence=[
                {
                    "id": "CONFIG_ERROR",
                    "description": "AI service not available",
                    "weight": 10,
                }
            ],
            tokens_used=0,
            cost_estimate=0.0,
            processing_time_ms=0,
            success=False,
            error_message=str(e),
        )


# Example usage
if __name__ == "__main__":
    # This would require a real email and API key
    print("AI service module loaded successfully")
    print(f"Model: {MODEL_NAME}")
    print(f"Input token limit: {INPUT_TOKEN_LIMIT}")
    print(f"Max retries: {MAX_RETRIES}")
