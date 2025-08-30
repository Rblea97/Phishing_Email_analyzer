# Security Policy

## 🛡️ Security Overview

The AI-Powered Phishing Detection System is built with security as a foundational principle. This document outlines our security measures, vulnerability reporting process, and best practices.

## 🔒 Security Features

### Application Security
- **Input Validation**: Comprehensive validation of all user inputs
- **File Upload Security**: Type validation, size limits, malware scanning
- **Rate Limiting**: 10 AI requests per minute per IP address
- **CSRF Protection**: Flask-WTF CSRF tokens on all forms
- **Secure Headers**: Security headers implemented via Flask-Talisman

### AI Integration Security
- **API Key Management**: Environment variables only, never logged
- **Token Limiting**: 4K token input limit with automatic truncation
- **Response Validation**: JSON schema validation for all AI responses
- **Timeout Protection**: 10-second timeout with retry limits
- **Cost Controls**: Daily spending monitoring and alerts

### Data Security
- **No PII to AI**: Only sanitized metadata sent to external APIs
- **Database Security**: Parameterized queries, SQL injection prevention
- **Audit Logging**: Complete analysis trail without sensitive data
- **Secure Storage**: Local database with appropriate file permissions

### Infrastructure Security
- **Environment Isolation**: Separate development/production environments
- **Secret Management**: Environment-based configuration
- **HTTPS Enforcement**: SSL/TLS in production deployment
- **Health Monitoring**: Comprehensive health checks with security status

## 🚨 Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 3.x     | ✅ Yes            |
| 2.x     | ✅ Yes (LTS)      |
| 1.x     | ❌ No             |

## 🔍 Security Testing

### Automated Security Checks
- **Input Validation Tests**: Malformed data handling
- **Rate Limiting Tests**: API abuse prevention
- **Authentication Tests**: Proper access controls
- **Cost Control Tests**: AI usage monitoring

### Manual Security Reviews
- **Code Reviews**: Security-focused peer review process
- **Dependency Scanning**: Regular vulnerability assessments
- **Penetration Testing**: Periodic security assessments

## 📋 Security Best Practices for Contributors

### Development Security
```python
# ✅ Good - Environment variable usage
api_key = os.getenv('OPENAI_API_KEY')

# ❌ Bad - Hardcoded secrets
api_key = "sk-abc123..."
```

### Input Validation
```python
# ✅ Good - Proper validation
def validate_email_file(file):
    if not file or file.filename == '':
        raise ValidationError("No file selected")
    
    allowed_extensions = {'.eml', '.txt', '.msg'}
    if not any(file.filename.endswith(ext) for ext in allowed_extensions):
        raise ValidationError("Invalid file type")
    
    if file.content_length > MAX_FILE_SIZE:
        raise ValidationError("File too large")

# ❌ Bad - No validation
def process_file(file):
    content = file.read()  # Dangerous!
```

### AI Integration Security
```python
# ✅ Good - Token limiting and validation
def prepare_ai_input(email_content: str) -> str:
    # Sanitize and truncate content
    sanitized = sanitize_email_content(email_content)
    return truncate_to_token_limit(sanitized, MAX_TOKENS)

# ❌ Bad - Direct AI submission
def analyze_with_ai(email_content: str):
    response = openai.chat.completions.create(
        messages=[{"role": "user", "content": email_content}]  # Unsafe!
    )
```

## 🚫 Security Anti-Patterns to Avoid

### Never Do This
- Store API keys in code or version control
- Log sensitive user data or email contents
- Send raw binary data to AI services
- Skip input validation for "internal" functions
- Use admin privileges for regular operations
- Expose detailed error messages to users

### Database Security
```python
# ✅ Good - Parameterized queries
cursor.execute("SELECT * FROM emails WHERE id = ?", (email_id,))

# ❌ Bad - SQL injection vulnerability  
cursor.execute(f"SELECT * FROM emails WHERE id = {email_id}")
```

## 🔐 Vulnerability Reporting

### Reporting Process
1. **Do not create public issues** for security vulnerabilities
2. Email security reports to: [Your security contact email]
3. Include detailed description and steps to reproduce
4. Allow 90 days for response before public disclosure
5. We will acknowledge receipt within 48 hours

### Report Template
```
Subject: Security Vulnerability in Phishing Detection System

**Vulnerability Type**: [e.g., Input Validation, Authentication Bypass]
**Severity**: [Critical/High/Medium/Low]
**Component**: [e.g., AI Integration, File Upload, Database]

**Description**:
[Detailed description of the vulnerability]

**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Impact**:
[Potential security impact]

**Suggested Fix**:
[If you have suggestions]

**Reporter**: [Your name/handle]
```

## 🛡️ Security Incident Response

### Response Timeline
- **0-2 hours**: Acknowledge receipt and begin assessment
- **2-24 hours**: Validate and classify severity
- **1-7 days**: Develop and test fix
- **7-14 days**: Deploy fix and notify reporter
- **30 days**: Public disclosure (if appropriate)

### Severity Classification
- **Critical**: Remote code execution, data breach
- **High**: Authentication bypass, privilege escalation
- **Medium**: Information disclosure, DoS attacks
- **Low**: Minor information leaks, timing attacks

## 🔧 Security Configuration

### Environment Variables (Required)
```bash
# Flask Security
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=production

# AI Security
OPENAI_API_KEY=sk-your-openai-api-key-here
MAX_DAILY_AI_COST=5.00

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
DAILY_ANALYSIS_LIMIT=100
```

### Production Security Checklist
- [ ] Environment variables configured securely
- [ ] Debug mode disabled (`FLASK_ENV=production`)
- [ ] HTTPS enforced with valid SSL certificate
- [ ] Rate limiting configured and tested
- [ ] Security headers implemented
- [ ] File upload restrictions in place
- [ ] Database access properly restricted
- [ ] Logging configured without sensitive data
- [ ] Health checks monitoring security status
- [ ] Backup and recovery procedures tested

## 📊 Security Monitoring

### Metrics to Monitor
- **Failed login attempts**: Authentication attacks
- **Rate limit violations**: API abuse attempts  
- **File upload rejections**: Malware upload attempts
- **AI cost spikes**: Potential abuse or DoS
- **Error rate increases**: Potential attacks
- **Unusual traffic patterns**: Suspicious activity

### Alerting Thresholds
- Rate limit violations > 100/hour
- AI cost > daily limit
- Error rate > 5%
- File upload rejections > 50/hour

## 🎓 Security Training Resources

### For Developers
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [AI Security Considerations](https://owasp.org/www-project-ai-security-and-privacy-guide/)

### Security Testing Tools
- `bandit` - Python security linter
- `safety` - Dependency vulnerability scanner  
- `semgrep` - Static analysis security tool
- `pytest-security` - Security testing framework

## 📞 Contact Information

- **Security Issues**: [Your security contact email]
- **General Questions**: [General contact]
- **Documentation**: This file and `/docs` folder

## 🏆 Security Hall of Fame

We appreciate responsible security researchers who help make our project safer:

- [Names of security researchers who reported vulnerabilities]

---

**Last Updated**: [Current Date]  
**Version**: 1.0  
**Next Review**: [Review Date]

*Security is everyone's responsibility. Thank you for helping keep the web safer! 🛡️*