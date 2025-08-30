"""
Email Parser Module for AI-Powered Phishing Detection System

Provides secure MIME parsing, URL extraction, and content normalization
with defense against malicious inputs and performance safeguards.
"""

import email
import email.policy
import email.utils
import hashlib
import logging
import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Tuple
from urllib.parse import unquote, urlparse

from html2text import HTML2Text

# Configure logging
logger = logging.getLogger(__name__)

# Security limits
MAX_PARSED_TEXT_SIZE = 1024 * 1024  # 1MB
MAX_PARSE_TIME = 30  # 30 seconds
MAX_URLS_PER_EMAIL = 500
MAX_HEADER_SIZE = 64 * 1024  # 64KB per header

# URL extraction regex (comprehensive but safe, including Unicode)
URL_REGEX = re.compile(
    r"http[s]?://(?:[\w]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", re.UNICODE
)

# Tracking parameter patterns to strip
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "msclkid",
    "_ga",
    "mc_cid",
    "mc_eid",
}


@dataclass
class ParsedURL:
    """Represents a parsed and normalized URL from email content"""

    original: str
    normalized: str
    domain: str
    path: str
    position: int
    context: str  # Surrounding text for context


@dataclass
class ParsedHeaders:
    """Represents extracted and validated email headers"""

    from_addr: str
    from_display: str
    to_addr: str
    reply_to: str
    return_path: str
    subject: str
    date: str
    received: List[str]
    authentication_results: str
    message_id: str
    other_headers: Dict[str, str]


@dataclass
class ParsedEmail:
    """Complete parsed email structure"""

    headers: ParsedHeaders
    text_body: str
    html_body: str
    html_as_text: str
    urls: List[ParsedURL]
    parse_time_ms: float
    security_warnings: List[str]
    raw_size: int
    parsed_size: int


class EmailParsingError(Exception):
    """Custom exception for email parsing errors"""

    pass


class EmailParser:
    """
    Secure email parser with MIME support and content extraction
    """

    def __init__(self):
        """Initialize parser with security-focused configuration"""
        self.html_parser = HTML2Text()
        self.html_parser.ignore_links = False
        self.html_parser.ignore_images = True
        self.html_parser.ignore_emphasis = False
        self.html_parser.body_width = 0  # No line wrapping
        self.html_parser.unicode_snob = True

    def parse_email(self, email_content: bytes, filename: str = "unknown") -> ParsedEmail:
        """
        Parse email content with comprehensive security checks

        Args:
            email_content: Raw email bytes
            filename: Original filename for logging

        Returns:
            ParsedEmail object with all extracted content

        Raises:
            EmailParsingError: If parsing fails or security limits exceeded
        """
        start_time = time.time()
        security_warnings = []

        try:
            # Size validation
            raw_size = len(email_content)
            if raw_size > 25 * 1024 * 1024:  # 25MB limit
                raise EmailParsingError(f"Email too large: {raw_size} bytes")

            logger.info(f"Parsing email '{filename}': {raw_size} bytes")

            # Parse with timeout protection
            msg = self._parse_with_timeout(email_content)

            # Extract headers
            headers = self._extract_headers(msg, security_warnings)

            # Extract body content
            text_body, html_body, html_as_text = self._extract_body(msg, security_warnings)

            # Extract URLs from all content
            urls = self._extract_urls(text_body, html_body, headers, security_warnings)

            # Calculate metrics
            parse_time_ms = (time.time() - start_time) * 1000
            parsed_size = len(text_body) + len(html_body)

            # Security size check
            if parsed_size > MAX_PARSED_TEXT_SIZE:
                security_warnings.append(
                    f"Parsed content truncated: {parsed_size} > {MAX_PARSED_TEXT_SIZE}"
                )
                text_body = text_body[: MAX_PARSED_TEXT_SIZE // 2]
                html_as_text = html_as_text[: MAX_PARSED_TEXT_SIZE // 2]

            logger.info(f"Email parsed successfully: {parse_time_ms:.1f}ms, {len(urls)} URLs")

            return ParsedEmail(
                headers=headers,
                text_body=text_body,
                html_body=html_body,
                html_as_text=html_as_text,
                urls=urls,
                parse_time_ms=parse_time_ms,
                security_warnings=security_warnings,
                raw_size=raw_size,
                parsed_size=parsed_size,
            )

        except Exception as e:
            logger.error(f"Email parsing failed for '{filename}': {str(e)}")
            raise EmailParsingError(f"Failed to parse email: {str(e)}")

    def _parse_with_timeout(self, email_content: bytes) -> email.message.EmailMessage:
        """Parse email with timeout protection"""
        start_time = time.time()

        try:
            # Use default policy for better parsing
            msg = email.message_from_bytes(email_content, policy=email.policy.default)

            # Check parsing time
            if time.time() - start_time > MAX_PARSE_TIME:
                raise EmailParsingError("Parsing timeout exceeded")

            return msg

        except Exception as e:
            raise EmailParsingError(f"MIME parsing failed: {str(e)}")

    def _extract_headers(
        self, msg: email.message.EmailMessage, warnings: List[str]
    ) -> ParsedHeaders:
        """Extract and validate email headers"""

        def safe_header(header_name: str) -> str:
            """Safely extract header with size limits"""
            try:
                value = msg.get(header_name, "")
                if len(value) > MAX_HEADER_SIZE:
                    warnings.append(f"Header '{header_name}' truncated")
                    value = value[:MAX_HEADER_SIZE]
                return self._clean_header_value(value)
            except Exception:
                return ""

        def parse_address(addr_str: str) -> Tuple[str, str]:
            """Parse email address into display name and email"""
            try:
                if not addr_str:
                    return "", ""

                parsed = email.utils.parseaddr(addr_str)
                display_name = self._clean_header_value(parsed[0])
                email_addr = self._clean_header_value(parsed[1])
                return display_name, email_addr
            except Exception:
                return "", addr_str

        # Extract From header
        from_header = safe_header("From")
        from_display, from_addr = parse_address(from_header)

        # Extract received headers (can be multiple)
        received_headers = []
        for received in msg.get_all("Received", []):
            if len(received_headers) >= 20:  # Limit to prevent abuse
                break
            received_headers.append(
                self._clean_header_value(received)[:1000]
            )  # Truncate long headers

        return ParsedHeaders(
            from_addr=from_addr,
            from_display=from_display,
            to_addr=parse_address(safe_header("To"))[1],
            reply_to=parse_address(safe_header("Reply-To"))[1],
            return_path=safe_header("Return-Path"),
            subject=safe_header("Subject"),
            date=safe_header("Date"),
            received=received_headers,
            authentication_results=safe_header("Authentication-Results"),
            message_id=safe_header("Message-ID"),
            other_headers={},  # Can extend for additional headers
        )

    def _extract_body(
        self, msg: email.message.EmailMessage, warnings: List[str]
    ) -> Tuple[str, str, str]:
        """Extract and clean email body content"""
        text_body = ""
        html_body = ""
        html_as_text = ""

        try:
            # Walk through message parts
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_maintype() == "multipart":
                        continue

                    content_type = part.get_content_type()

                    try:
                        payload = part.get_payload(decode=True)
                        if not payload:
                            continue

                        # Decode bytes to string safely
                        if isinstance(payload, bytes):
                            charset = part.get_content_charset("utf-8")
                            try:
                                content = payload.decode(charset, errors="replace")
                            except (UnicodeDecodeError, LookupError):
                                content = payload.decode("utf-8", errors="replace")
                        else:
                            content = str(payload)

                        # Size check
                        if len(content) > MAX_PARSED_TEXT_SIZE:
                            warnings.append(f"Part content truncated: {content_type}")
                            content = content[:MAX_PARSED_TEXT_SIZE]

                        if content_type == "text/plain":
                            text_body += content + "\n"
                        elif content_type == "text/html":
                            html_body += content + "\n"

                    except Exception as e:
                        warnings.append(f"Failed to decode part {content_type}: {str(e)}")
                        continue
            else:
                # Single part message
                content_type = msg.get_content_type()
                try:
                    payload = msg.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        charset = msg.get_content_charset("utf-8")
                        try:
                            content = payload.decode(charset, errors="replace")
                        except (UnicodeDecodeError, LookupError):
                            content = payload.decode("utf-8", errors="replace")
                    else:
                        content = str(payload)

                    if content_type == "text/plain":
                        text_body = content
                    elif content_type == "text/html":
                        html_body = content

                except Exception as e:
                    warnings.append(f"Failed to decode single part: {str(e)}")

            # Convert HTML to text safely
            if html_body:
                try:
                    html_as_text = self.html_parser.handle(html_body)
                    # Additional cleaning
                    html_as_text = self._clean_text_content(html_as_text)
                except Exception as e:
                    warnings.append(f"HTML to text conversion failed: {str(e)}")
                    html_as_text = ""

            # Clean text content
            text_body = self._clean_text_content(text_body)

        except Exception as e:
            warnings.append(f"Body extraction failed: {str(e)}")

        return text_body, html_body, html_as_text

    def _extract_urls(
        self,
        text_body: str,
        html_body: str,
        headers: ParsedHeaders,
        warnings: List[str],
    ) -> List[ParsedURL]:
        """Extract and normalize URLs from email content"""
        urls = []
        url_set = set()  # For deduplication

        # Search contexts: text body, html body, and key headers
        search_contexts = [
            ("text_body", text_body),
            ("html_body", html_body),
            ("subject", headers.subject),
            ("return_path", headers.return_path),
        ]

        for context_name, content in search_contexts:
            if not content:
                continue

            try:
                # Find URLs using regex
                for match in URL_REGEX.finditer(content):
                    if len(urls) >= MAX_URLS_PER_EMAIL:
                        warnings.append(f"URL limit reached: {MAX_URLS_PER_EMAIL}")
                        break

                    original_url = match.group(0)
                    position = match.start()

                    # Get surrounding context (20 chars before and after)
                    start_context = max(0, position - 20)
                    end_context = min(len(content), position + len(original_url) + 20)
                    context = content[start_context:end_context].replace("\n", " ")

                    # Normalize URL
                    normalized_url = self._normalize_url(original_url)

                    # Skip duplicates
                    if normalized_url in url_set:
                        continue
                    url_set.add(normalized_url)

                    # Parse domain safely
                    try:
                        parsed = urlparse(normalized_url)
                        domain = parsed.netloc.lower()
                        path = parsed.path
                    except Exception:
                        domain = "invalid"
                        path = ""

                    parsed_url = ParsedURL(
                        original=original_url,
                        normalized=normalized_url,
                        domain=domain,
                        path=path,
                        position=position,
                        context=context,
                    )

                    urls.append(parsed_url)

            except Exception as e:
                warnings.append(f"URL extraction failed for {context_name}: {str(e)}")

        logger.debug(f"Extracted {len(urls)} unique URLs")
        return urls

    def _normalize_url(self, url: str) -> str:
        """Normalize URL with security considerations"""
        try:
            # Parse URL
            parsed = urlparse(url)

            # Convert to lowercase domain
            domain = parsed.netloc.lower()

            # Decode punycode if present
            try:
                if domain.startswith("xn--") or ".xn--" in domain:
                    domain = domain.encode("ascii").decode("idna")
            except Exception:
                pass  # Keep original if decoding fails

            # Remove tracking parameters
            query_params = []
            if parsed.query:
                params = parsed.query.split("&")
                for param in params:
                    if "=" in param:
                        key = param.split("=")[0].lower()
                        if key not in TRACKING_PARAMS:
                            query_params.append(param)
                    else:
                        query_params.append(param)

            # Reconstruct URL
            clean_query = "&".join(query_params) if query_params else ""

            # URL decode path safely
            try:
                path = unquote(parsed.path)
            except Exception:
                path = parsed.path

            normalized = f"{parsed.scheme}://{domain}{path}"
            if clean_query:
                normalized += f"?{clean_query}"
            if parsed.fragment:
                normalized += f"#{parsed.fragment}"

            return normalized

        except Exception:
            # Return original URL if normalization fails
            return url

    def _clean_header_value(self, value: str) -> str:
        """Clean and validate header value"""
        if not value:
            return ""

        # Decode MIME encoded words
        try:
            decoded = email.header.decode_header(value)
            parts = []
            for part, encoding in decoded:
                if isinstance(part, bytes):
                    if encoding:
                        try:
                            part = part.decode(encoding, errors="replace")
                        except (UnicodeDecodeError, LookupError):
                            part = part.decode("utf-8", errors="replace")
                    else:
                        part = part.decode("utf-8", errors="replace")
                parts.append(part)
            value = "".join(parts)
        except Exception:
            pass  # Use original value if decoding fails

        # Normalize unicode and strip
        value = unicodedata.normalize("NFKC", value)
        value = value.strip()

        # Remove control characters except basic whitespace
        cleaned = ""
        for char in value:
            if char in "\t\n\r " or not unicodedata.category(char).startswith("C"):
                cleaned += char

        return cleaned

    def _clean_text_content(self, content: str) -> str:
        """Clean text content with security considerations"""
        if not content:
            return ""

        # Normalize unicode
        content = unicodedata.normalize("NFKC", content)

        # Remove excessive whitespace while preserving structure
        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            # Strip line but preserve intentional spacing
            line = line.rstrip()
            cleaned_lines.append(line)

        # Join lines and limit consecutive newlines
        content = "\n".join(cleaned_lines)
        content = re.sub(r"\n{3,}", "\n\n", content)  # Max 2 consecutive newlines

        return content.strip()


def get_email_hash(email_content: bytes) -> str:
    """Generate SHA-256 hash of email content"""
    return hashlib.sha256(email_content).hexdigest()


# Convenience function for external use
def parse_email_content(email_content: bytes, filename: str = "unknown") -> ParsedEmail:
    """
    Parse email content using the EmailParser

    Args:
        email_content: Raw email bytes
        filename: Original filename for logging

    Returns:
        ParsedEmail object with extracted content
    """
    parser = EmailParser()
    return parser.parse_email(email_content, filename)
