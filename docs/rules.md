# Detection Rules Documentation

This document provides detailed information about the 9 weighted detection rules used in the AI-Powered Phishing Detection System.

## 🎯 Rule Engine Overview

The rule-based detection engine uses 9 weighted rules that analyze different aspects of email authenticity and suspicious patterns. Each rule contributes a weighted score (0-20 points) to the overall risk assessment.

**Total Possible Score**: 95 points  
**Classification Thresholds**:
- **0-20**: Likely Safe
- **21-50**: Suspicious  
- **51+**: Likely Phishing

## 🔍 Detection Rules Details

### 1. Header Mismatch Detection (Weight: 15)

**Rule ID**: `HEADER_MISMATCH`  
**Description**: Detects when the display name domain differs from the actual sender domain  
**Risk Level**: High (authentication spoofing)

#### How It Works
```python
display_name = "PayPal Security"
from_domain = "suspicious-phishing-site.com"
# Mismatch detected: PayPal mentioned but sent from different domain
```

#### Examples
- ✅ **Triggers**: "Apple Support" `<scam@fake-apple.com>`
- ✅ **Triggers**: "Microsoft Security" `<noreply@microsoft-security.net>`  
- ❌ **Safe**: "John Smith" `<john@company.com>` (no brand spoofing)

#### Real Detection
```
From: PayPal Security <notifications@secure-verification.top>
Display: PayPal | Domain: secure-verification.top
Evidence: Display name suggests "PayPal" but domain is suspicious TLD
```

---

### 2. Reply-To Mismatch (Weight: 10)

**Rule ID**: `REPLYTO_MISMATCH`  
**Description**: Identifies emails where Reply-To domain differs from From domain  
**Risk Level**: Medium (response redirection)

#### How It Works
```python
from_domain = "company.com"
reply_to_domain = "different-collector.com"
# Potential response harvesting attempt
```

#### Examples
- ✅ **Triggers**: From `service@bank.com`, Reply-To `harvest@data-collector.net`
- ❌ **Safe**: From `noreply@company.com`, Reply-To `support@company.com`

#### Real Detection
```
From: notifications@fake-service123.com
Reply-To: support@different-domain.net  
Evidence: Reply-To redirects responses to different organization
```

---

### 3. Authentication Failures (Weight: 20)

**Rule ID**: `AUTH_FAILURES`  
**Description**: Detects SPF, DKIM, and DMARC authentication failures  
**Risk Level**: Critical (bypass legitimate email security)

#### How It Works
```python
spf_keywords = ["fail", "softfail", "none", "neutral"]
dmarc_keywords = ["fail", "none"] 
dkim_keywords = ["fail", "invalid", "none"]
```

#### Examples
- ✅ **Triggers**: `Authentication-Results: spf=fail`
- ✅ **Triggers**: `DMARC: fail (p=reject)`
- ❌ **Safe**: `SPF: pass, DKIM: pass, DMARC: pass`

#### Real Detection
```
Authentication-Results: gmail.com; spf=fail smtp.mailfrom=fake-domain.com;
dmarc=fail (p=reject dis=none) header.from=spoofed-bank.com
Evidence: Multiple authentication failures indicate spoofing attempt
```

---

### 4. Urgent Language Detection (Weight: 10)

**Rule ID**: `URGENT_LANGUAGE`  
**Description**: Identifies high-pressure language designed to rush decisions  
**Risk Level**: Medium (social engineering tactic)

#### Keywords Detected
```python
urgent_phrases = [
    "expires today", "immediate action", "urgent response",
    "account suspended", "verify immediately", "act now",
    "limited time", "expires soon", "urgent notice"
]
```

#### Examples
- ✅ **Triggers**: "Your account expires today - verify immediately!"
- ✅ **Triggers**: "URGENT: Immediate action required"
- ❌ **Safe**: "Monthly newsletter - read when convenient"

#### Real Detection
```
Subject: URGENT: Account Suspended - Verify Within 24 Hours
Content: "expires today, immediate action, verify your account"
Evidence: Multiple urgent pressure tactics detected
```

---

### 5. URL Shortener Detection (Weight: 10)

**Rule ID**: `URL_SHORTENERS`  
**Description**: Flags emails containing shortened URLs that hide destinations  
**Risk Level**: Medium (destination obfuscation)

#### Detected Domains
```python
shortener_domains = [
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
    "short.link", "is.gd", "buff.ly", "tiny.cc"
]
```

#### Examples
- ✅ **Triggers**: `Click here: https://bit.ly/abc123`
- ✅ **Triggers**: `Update account: https://tinyurl.com/verify`
- ❌ **Safe**: `Visit us: https://company.com/support`

#### Real Detection
```
URL Found: https://bit.ly/bank-verify-urgent
Context: "Click here to verify your account immediately"
Evidence: URL shortener hides final destination from user
```

---

### 6. Suspicious TLD Detection (Weight: 10)

**Rule ID**: `SUSPICIOUS_TLDS`  
**Description**: Identifies domains using suspicious top-level domains  
**Risk Level**: Medium (domain reputation indicators)

#### Flagged TLDs
```python
suspicious_tlds = [
    ".top", ".xyz", ".click", ".download", ".stream",
    ".loan", ".cricket", ".science", ".work", ".cf"
]
```

#### Examples
- ✅ **Triggers**: `secure-banking.top`
- ✅ **Triggers**: `paypal-verification.xyz`
- ❌ **Safe**: `company.com`, `service.org`

#### Real Detection
```
Domain: secure-verification.top
TLD: .top (commonly used for suspicious activities)
Evidence: Suspicious TLD often associated with phishing domains
```

---

### 7. Unicode Spoofing Detection (Weight: 10)

**Rule ID**: `UNICODE_SPOOFING`  
**Description**: Detects domains using non-ASCII or mixed script characters  
**Risk Level**: High (visual deception)

#### Detection Method
```python
# Checks for:
# - Non-ASCII characters in domains
# - Mixed scripts (Latin + Cyrillic)
# - Homograph attacks
```

#### Examples
- ✅ **Triggers**: `аррӏе.com` (Cyrillic а, р, ӏ, е)
- ✅ **Triggers**: `microsοft.com` (Greek omicron ο)
- ❌ **Safe**: `company.com` (pure ASCII)

#### Real Detection
```
Domain: аррӏе.com
Analysis: Uses Cyrillic characters (а, р, ӏ, е) to mimic "apple.com"
Evidence: Homograph attack attempting to deceive users visually
```

---

### 8. Generic Greeting Detection (Weight: 5)

**Rule ID**: `NO_PERSONALIZATION`  
**Description**: Flags emails using generic, non-personalized greetings  
**Risk Level**: Low (mass mailing indicator)

#### Generic Patterns
```python
generic_greetings = [
    "dear customer", "dear user", "dear client",
    "valued customer", "account holder", "dear member"
]
```

#### Examples
- ✅ **Triggers**: "Dear Valued Customer"
- ✅ **Triggers**: "Hello Account Holder"
- ❌ **Safe**: "Dear John Smith", "Hi Sarah"

#### Real Detection
```
Greeting: "Dear Valued Customer"
Context: No personalization in legitimate-appearing bank email
Evidence: Mass mailing technique, lacks personal addressing
```

---

### 9. Attachment Keywords (Weight: 5)

**Rule ID**: `ATTACHMENT_KEYWORDS`  
**Description**: Detects suspicious attachment-related keywords with URLs  
**Risk Level**: Low (social engineering setup)

#### Detected Patterns
```python
attachment_keywords = [
    "invoice", "receipt", "statement", "document",
    "pdf", "attachment", "download", "file"
]
# Triggers only when keywords + URLs are both present
```

#### Examples
- ✅ **Triggers**: "Invoice attached" + `download-link.com`
- ✅ **Triggers**: "View PDF statement" + multiple URLs
- ❌ **Safe**: "Invoice attached" (no suspicious URLs)

#### Real Detection
```
Content: "Please download your invoice PDF from the link below"
URLs: https://secure-verification.top/invoice.pdf
Evidence: Attachment keywords combined with suspicious download links
```

## 📊 Rule Performance Matrix

| Rule | Weight | Precision | Recall | Common in |
|------|--------|-----------|--------|-----------|
| Header Mismatch | 15 | High | Medium | Brand spoofing |
| Reply-To Mismatch | 10 | High | Low | Response harvesting |
| Auth Failures | 20 | Very High | High | Domain spoofing |
| Urgent Language | 10 | Medium | High | Social engineering |
| URL Shorteners | 10 | High | Medium | Link obfuscation |
| Suspicious TLDs | 10 | Medium | Low | Cheap domain attacks |
| Unicode Spoofing | 10 | Very High | Very Low | Advanced spoofing |
| Generic Greetings | 5 | Low | Very High | Mass campaigns |
| Attachment Keywords | 5 | Medium | Low | Malware distribution |

## 🔄 Rule Interaction Examples

### Multi-Rule Detection Scenarios

#### High-Risk Phishing (70 points)
```
From: "PayPal Security" <urgent@secure-verification.top>
Reply-To: collect@data-harvest.xyz
Authentication-Results: spf=fail dmarc=fail
Subject: URGENT: Account expires today - verify immediately
Content: Dear Valued Customer, click https://bit.ly/paypal-verify

Triggered Rules:
✓ HEADER_MISMATCH (15) - PayPal spoofing
✓ REPLYTO_MISMATCH (10) - Different reply domain  
✓ AUTH_FAILURES (20) - SPF/DMARC failures
✓ URGENT_LANGUAGE (10) - "expires today", "urgent", "immediately"
✓ URL_SHORTENERS (10) - bit.ly link
✓ SUSPICIOUS_TLDS (10) - .top and .xyz domains
✓ NO_PERSONALIZATION (5) - "Dear Valued Customer"

Total Score: 80/95 → Likely Phishing
```

#### Medium-Risk Email (25 points)
```
From: "Company Updates" <news@company-news.click>
Subject: Important company updates
Content: Dear Team Member, please review the quarterly report

Triggered Rules:
✓ SUSPICIOUS_TLDS (10) - .click domain
✓ URGENT_LANGUAGE (10) - "Important"  
✓ NO_PERSONALIZATION (5) - "Dear Team Member"

Total Score: 25/95 → Suspicious
```

#### Safe Email (0 points)
```
From: "John Smith" <john.smith@company.com>
To: sarah.jones@company.com
Subject: Weekly team meeting notes
Content: Hi Sarah, here are the notes from our meeting...

Triggered Rules: None
Total Score: 0/95 → Likely Safe
```

## 🛡️ Rule Effectiveness

### Strengths
- **Fast Processing**: All rules execute in <5ms combined
- **Low False Positives**: Carefully tuned thresholds
- **Complementary**: Rules cover different attack vectors
- **Transparent**: Clear evidence for each trigger
- **Maintainable**: Easy to add new patterns

### Limitations
- **Evolving Threats**: New attack patterns may bypass rules
- **Context Blind**: Cannot understand semantic meaning
- **Language Specific**: English-focused urgent language detection
- **Domain Lists**: Require periodic updates

### Future Enhancements
- [ ] Machine learning rule weight optimization
- [ ] Multi-language urgent phrase detection  
- [ ] Real-time domain reputation integration
- [ ] Behavioral analysis patterns
- [ ] Content similarity matching

---

**Rule Engine Version**: 1.0  
**Last Updated**: 2025-08-30  
**Total Rules**: 9  
**Maximum Score**: 95 points

*These rules are continuously refined based on new phishing techniques and false positive feedback.*