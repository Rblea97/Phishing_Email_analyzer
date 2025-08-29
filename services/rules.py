"""
Rule-Based Detection Engine for AI-Powered Phishing Detection System

Implements weighted rule system for phishing detection with extensible
architecture and comprehensive evidence tracking.
"""

import re
import time
import logging
import unicodedata
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
from .parser import ParsedEmail, ParsedURL

# Configure logging
logger = logging.getLogger(__name__)

# URL shortener domains (common ones)
URL_SHORTENERS = {
    'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 
    'buff.ly', 'adf.ly', 'short.link', 'tiny.cc', 'rb.gy',
    'cutt.ly', 'short.io', 'rebrandly.com', 'clck.ru'
}

# Suspicious TLDs (frequently abused)
SUSPICIOUS_TLDS = {
    '.top', '.xyz', '.click', '.cam', '.zip', '.download',
    '.work', '.men', '.date', '.racing', '.loan', '.science',
    '.cf', '.tk', '.ml', '.ga', '.country', '.stream'
}

# Urgent language patterns
URGENT_PATTERNS = [
    r'\burgent\b', r'\bimmediate\s+action\b', r'\bexpires?\s+today\b',
    r'\bverify\s+your\s+account\b', r'\bsuspend(?:ed)?\s+account\b',
    r'\bact\s+now\b', r'\btime\s+sensitive\b', r'\blimited\s+time\b',
    r'\b24\s+hours?\b', r'\bexpir(?:e|ing)\s+soon\b'
]

# Generic greeting patterns
GENERIC_GREETINGS = [
    r'\bdear\s+(?:user|customer|client|member|sir|madam)\b',
    r'\bvalued\s+(?:customer|client|member)\b',
    r'\bhello\s+(?:user|customer|there)\b',
    r'\bgreetings?\s+(?:user|customer)?\b'
]

# Attachment/payment related keywords
ATTACHMENT_KEYWORDS = [
    'invoice', 'payment', 'receipt', 'bill', 'statement',
    'document', 'attachment', 'pdf', 'download', 'password'
]

# Authentication failure patterns
AUTH_FAIL_PATTERNS = [
    r'spf\s*=\s*(?:fail|softfail|none)',
    r'dkim\s*=\s*(?:fail|none)',
    r'dmarc\s*=\s*(?:fail|none)',
    r'authentication-results:.*(?:fail|none)',
]


@dataclass
class RuleEvidence:
    """Evidence for a fired rule"""
    rule_id: str
    description: str
    weight: int
    details: str
    matched_content: Optional[str] = None


@dataclass
class DetectionResult:
    """Complete detection analysis result"""
    score: int
    label: str
    confidence: float
    evidence: List[RuleEvidence]
    processing_time_ms: float
    rules_checked: int
    rules_fired: int


class Rule:
    """Base class for phishing detection rules"""
    
    def __init__(self, rule_id: str, description: str, weight: int):
        self.rule_id = rule_id
        self.description = description
        self.weight = weight
    
    def check(self, parsed_email: ParsedEmail) -> Optional[RuleEvidence]:
        """
        Check if rule applies to email
        
        Returns:
            RuleEvidence if rule fires, None otherwise
        """
        raise NotImplementedError
    
    def _extract_domain_from_email(self, email_addr: str) -> str:
        """Extract domain from email address"""
        if '@' in email_addr:
            return email_addr.split('@')[-1].lower().strip()
        return ""
    
    def _extract_domain_from_display_name(self, display_name: str) -> str:
        """Extract domain from display name if it contains one"""
        # Look for domain-like patterns in display name
        domain_pattern = r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(domain_pattern, display_name.lower())
        return matches[0] if matches else ""


class HeaderMismatchRule(Rule):
    """Detect mismatch between display name and From domain"""
    
    def __init__(self):
        super().__init__(
            "HEADER_MISMATCH",
            "Display name domain differs from From domain",
            15
        )
    
    def check(self, parsed_email: ParsedEmail) -> Optional[RuleEvidence]:
        headers = parsed_email.headers
        
        if not headers.from_display or not headers.from_addr:
            return None
        
        from_domain = self._extract_domain_from_email(headers.from_addr)
        display_domain = self._extract_domain_from_display_name(headers.from_display)
        
        if display_domain and from_domain and display_domain != from_domain:
            return RuleEvidence(
                rule_id=self.rule_id,
                description=self.description,
                weight=self.weight,
                details=f"Display name suggests '{display_domain}' but From address is '{from_domain}'",
                matched_content=f"Display: '{headers.from_display}', From: '{headers.from_addr}'"
            )
        
        return None


class ReplyToMismatchRule(Rule):
    """Detect mismatch between Reply-To and From domains"""
    
    def __init__(self):
        super().__init__(
            "REPLYTO_MISMATCH",
            "Reply-To domain differs from From domain", 
            10
        )
    
    def check(self, parsed_email: ParsedEmail) -> Optional[RuleEvidence]:
        headers = parsed_email.headers
        
        if not headers.reply_to or not headers.from_addr:
            return None
        
        from_domain = self._extract_domain_from_email(headers.from_addr)
        reply_domain = self._extract_domain_from_email(headers.reply_to)
        
        if from_domain and reply_domain and from_domain != reply_domain:
            return RuleEvidence(
                rule_id=self.rule_id,
                description=self.description,
                weight=self.weight,
                details=f"From domain '{from_domain}' != Reply-To domain '{reply_domain}'",
                matched_content=f"From: {headers.from_addr}, Reply-To: {headers.reply_to}"
            )
        
        return None


class AuthFailureRule(Rule):
    """Detect authentication failures in headers"""
    
    def __init__(self):
        super().__init__(
            "AUTH_FAIL_HINTS",
            "Authentication-Results indicates SPF/DKIM/DMARC failure",
            20
        )
    
    def check(self, parsed_email: ParsedEmail) -> Optional[RuleEvidence]:
        auth_results = parsed_email.headers.authentication_results.lower()
        
        if not auth_results:
            return None
        
        failures = []
        for pattern in AUTH_FAIL_PATTERNS:
            matches = re.findall(pattern, auth_results, re.IGNORECASE)
            if matches:
                failures.extend(matches)
        
        if failures:
            return RuleEvidence(
                rule_id=self.rule_id,
                description=self.description,
                weight=self.weight,
                details=f"Authentication failures detected: {', '.join(set(failures))}",
                matched_content=auth_results[:200]  # Truncate for display
            )
        
        return None


class UrgentLanguageRule(Rule):
    """Detect urgent/pressure language patterns"""
    
    def __init__(self):
        super().__init__(
            "URGENT_LANGUAGE",
            "Contains urgent or pressure language",
            10
        )
    
    def check(self, parsed_email: ParsedEmail) -> Optional[RuleEvidence]:
        # Combine subject and body text for analysis
        text_to_check = f"{parsed_email.headers.subject} {parsed_email.text_body} {parsed_email.html_as_text}"
        text_to_check = text_to_check.lower()
        
        matches = []
        for pattern in URGENT_PATTERNS:
            found = re.findall(pattern, text_to_check, re.IGNORECASE)
            if found:
                matches.extend(found)
        
        if matches:
            unique_matches = list(set(matches))
            return RuleEvidence(
                rule_id=self.rule_id,
                description=self.description,
                weight=self.weight,
                details=f"Urgent language detected: {', '.join(unique_matches[:5])}",  # Limit display
                matched_content=', '.join(unique_matches)
            )
        
        return None


class URLShortenerRule(Rule):
    """Detect URL shortening services"""
    
    def __init__(self):
        super().__init__(
            "URL_SHORTENER",
            "Contains URLs from shortening services",
            10
        )
    
    def check(self, parsed_email: ParsedEmail) -> Optional[RuleEvidence]:
        shortener_urls = []
        
        for url in parsed_email.urls:
            if url.domain in URL_SHORTENERS:
                shortener_urls.append(url.domain)
        
        if shortener_urls:
            unique_shorteners = list(set(shortener_urls))
            return RuleEvidence(
                rule_id=self.rule_id,
                description=self.description,
                weight=self.weight,
                details=f"URL shorteners found: {', '.join(unique_shorteners)}",
                matched_content=', '.join(unique_shorteners)
            )
        
        return None


class SuspiciousTLDRule(Rule):
    """Detect suspicious top-level domains"""
    
    def __init__(self):
        super().__init__(
            "SUSPICIOUS_TLDS",
            "Contains URLs with suspicious TLDs",
            10
        )
    
    def check(self, parsed_email: ParsedEmail) -> Optional[RuleEvidence]:
        suspicious_domains = []
        
        for url in parsed_email.urls:
            domain = url.domain.lower()
            for tld in SUSPICIOUS_TLDS:
                if domain.endswith(tld):
                    suspicious_domains.append(f"{domain} ({tld})")
                    break
        
        if suspicious_domains:
            return RuleEvidence(
                rule_id=self.rule_id,
                description=self.description,
                weight=self.weight,
                details=f"Suspicious TLDs found: {', '.join(suspicious_domains[:5])}",
                matched_content=', '.join(suspicious_domains)
            )
        
        return None


class UnicodeSpoofRule(Rule):
    """Detect basic Unicode spoofing attempts"""
    
    def __init__(self):
        super().__init__(
            "UNICODE_SPOOF",
            "Potential Unicode spoofing in domains",
            10
        )
    
    def check(self, parsed_email: ParsedEmail) -> Optional[RuleEvidence]:
        suspicious_domains = []
        
        for url in parsed_email.urls:
            domain = url.domain
            
            # Check for non-ASCII characters
            if not domain.isascii():
                suspicious_domains.append(f"{domain} (non-ASCII)")
                continue
            
            # Check for mixed scripts (basic detection)
            if self._has_mixed_scripts(domain):
                suspicious_domains.append(f"{domain} (mixed-script)")
        
        if suspicious_domains:
            return RuleEvidence(
                rule_id=self.rule_id,
                description=self.description,
                weight=self.weight,
                details=f"Suspicious domains: {', '.join(suspicious_domains[:3])}",
                matched_content=', '.join(suspicious_domains)
            )
        
        return None
    
    def _has_mixed_scripts(self, domain: str) -> bool:
        """Basic mixed script detection"""
        scripts = set()
        for char in domain:
            if char.isalpha():
                script = unicodedata.name(char, '').split()[0]
                scripts.add(script)
                if len(scripts) > 1:
                    return True
        return False


class NoPersonalizationRule(Rule):
    """Detect generic, non-personalized greetings"""
    
    def __init__(self):
        super().__init__(
            "NO_PERSONALIZATION",
            "Uses generic greetings without personalization",
            5
        )
    
    def check(self, parsed_email: ParsedEmail) -> Optional[RuleEvidence]:
        text_to_check = f"{parsed_email.text_body} {parsed_email.html_as_text}".lower()
        
        matches = []
        for pattern in GENERIC_GREETINGS:
            found = re.findall(pattern, text_to_check, re.IGNORECASE)
            if found:
                matches.extend(found)
        
        if matches:
            unique_matches = list(set(matches))
            return RuleEvidence(
                rule_id=self.rule_id,
                description=self.description,
                weight=self.weight,
                details=f"Generic greetings: {', '.join(unique_matches[:3])}",
                matched_content=', '.join(unique_matches)
            )
        
        return None


class AttachmentKeywordsRule(Rule):
    """Detect attachment-related keywords with links"""
    
    def __init__(self):
        super().__init__(
            "ATTACHMENT_KEYWORDS",
            "Mentions attachments/payments with links present",
            5
        )
    
    def check(self, parsed_email: ParsedEmail) -> Optional[RuleEvidence]:
        if not parsed_email.urls:  # No URLs, so no risk
            return None
        
        text_to_check = f"{parsed_email.headers.subject} {parsed_email.text_body} {parsed_email.html_as_text}".lower()
        
        found_keywords = []
        for keyword in ATTACHMENT_KEYWORDS:
            if keyword in text_to_check:
                found_keywords.append(keyword)
        
        if found_keywords and len(parsed_email.urls) > 0:
            return RuleEvidence(
                rule_id=self.rule_id,
                description=self.description,
                weight=self.weight,
                details=f"Keywords '{', '.join(found_keywords[:3])}' with {len(parsed_email.urls)} URLs",
                matched_content=', '.join(found_keywords)
            )
        
        return None


class RuleEngine:
    """
    Main rule engine for phishing detection
    """
    
    def __init__(self):
        """Initialize with default rule set"""
        self.rules = [
            HeaderMismatchRule(),
            ReplyToMismatchRule(),
            AuthFailureRule(),
            UrgentLanguageRule(),
            URLShortenerRule(),
            SuspiciousTLDRule(),
            UnicodeSpoofRule(),
            NoPersonalizationRule(),
            AttachmentKeywordsRule()
        ]
        
        logger.info(f"Rule engine initialized with {len(self.rules)} rules")
    
    def analyze_email(self, parsed_email: ParsedEmail) -> DetectionResult:
        """
        Run all rules against parsed email
        
        Args:
            parsed_email: ParsedEmail object from parser
            
        Returns:
            DetectionResult with score, label, and evidence
        """
        start_time = time.time()
        
        evidence = []
        total_score = 0
        
        logger.debug(f"Analyzing email with {len(self.rules)} rules")
        
        # Run each rule
        for rule in self.rules:
            try:
                result = rule.check(parsed_email)
                if result:
                    evidence.append(result)
                    total_score += result.weight
                    logger.debug(f"Rule {rule.rule_id} fired: {result.weight} points")
                    
            except Exception as e:
                logger.error(f"Rule {rule.rule_id} failed: {str(e)}")
                continue
        
        # Cap score at 100
        final_score = min(total_score, 100)
        
        # Determine label and confidence
        label, confidence = self._calculate_label_and_confidence(final_score, len(evidence))
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"Email analysis complete: score={final_score}, label={label}, "
                   f"evidence={len(evidence)}, time={processing_time:.1f}ms")
        
        return DetectionResult(
            score=final_score,
            label=label,
            confidence=confidence,
            evidence=evidence,
            processing_time_ms=processing_time,
            rules_checked=len(self.rules),
            rules_fired=len(evidence)
        )
    
    def _calculate_label_and_confidence(self, score: int, evidence_count: int) -> tuple[str, float]:
        """Calculate risk label and confidence based on score and evidence"""
        
        # Base confidence on evidence count and score consistency
        base_confidence = min(0.95, 0.5 + (evidence_count * 0.1))
        
        # Adjust confidence based on score ranges
        if score >= 60:
            label = "Likely Phishing"
            confidence = base_confidence
        elif score >= 30:
            label = "Suspicious"
            confidence = base_confidence * 0.8  # Lower confidence for borderline cases
        else:
            label = "Likely Safe"
            confidence = max(0.6, 1.0 - (score / 30.0))  # Higher confidence for low scores
        
        return label, round(confidence, 2)
    
    def add_rule(self, rule: Rule) -> None:
        """Add a new rule to the engine"""
        self.rules.append(rule)
        logger.info(f"Added rule {rule.rule_id}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID"""
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                del self.rules[i]
                logger.info(f"Removed rule {rule_id}")
                return True
        return False
    
    def get_rule_info(self) -> Dict[str, Any]:
        """Get information about all loaded rules"""
        return {
            "total_rules": len(self.rules),
            "rules": [
                {
                    "id": rule.rule_id,
                    "description": rule.description,
                    "weight": rule.weight
                }
                for rule in self.rules
            ]
        }


# Convenience function for external use
def analyze_email(parsed_email: ParsedEmail) -> DetectionResult:
    """
    Analyze parsed email using default rule engine
    
    Args:
        parsed_email: ParsedEmail object
        
    Returns:
        DetectionResult with analysis results
    """
    engine = RuleEngine()
    return engine.analyze_email(parsed_email)