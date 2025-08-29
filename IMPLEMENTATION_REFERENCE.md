# AI-Powered Phishing Detection - Implementation Reference

*Comprehensive technical reference for phase-by-phase development*

## 🎯 Project Overview

**Goal**: Build an AI-powered phishing email detection system demonstrating practical cybersecurity and machine learning skills through a working live demo.

**Key Success Metrics**: 
- >90% accuracy on known phishing samples
- Live demo deployed on Railway (always accessible)
- Professional documentation and portfolio presentation
- Enterprise-grade security implementation

---

## 🏗️ System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface (Flask)                    │
│              File Upload | Dashboard | Auth                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                API Gateway & Rate Limiting                  │
│            Authentication | Cost Control                    │
└─┬─────────────┬─────────────────────┬─────────────────────┬─┘
  │             │                     │                     │
┌─▼───────────┐ │ ┌─────────────────▼─┐ ┌─────────────────▼─┐
│Email Parser │ │ │  AI Analysis      │ │  URL Scanner      │
│- Headers    │ │ │  - GPT-4o-mini    │ │  - Safe Browsing  │
│- Content    │ │ │  - DistilBERT     │ │  - URLVoid        │
│- Metadata   │ │ │  - Ensemble       │ │  - Pattern Check  │
└─────────────┘ │ └───────────────────┘ └───────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│                    Data Layer                               │
│    SQLite/PostgreSQL | Redis Cache | File Storage          │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack Evolution

**Phase 1-3 (MVP):**
- Flask + SQLite + Railway
- OpenAI GPT-4o-mini API
- Basic authentication
- File-based storage

**Phase 4-7 (Production):**
- Flask/FastAPI + PostgreSQL + Docker
- Local DistilBERT models
- JWT authentication + Redis sessions
- Cloud storage integration

---

## 🔒 Security Implementation Guide

### OWASP Checklist by Phase

**Phase 1-2 (Foundation Security):**
- [ ] Environment variables for all secrets (.env + .gitignore)
- [ ] Input validation on file uploads (size limits: 25MB)
- [ ] Secure filename handling (Werkzeug secure_filename)
- [ ] XSS protection in templates (Jinja2 auto-escaping)
- [ ] CSRF protection (Flask-WTF)

**Phase 3-4 (Authentication Security):**
- [ ] bcrypt password hashing (min 12 rounds)
- [ ] JWT token management (proper expiration)
- [ ] Session security (secure cookies, HTTPOnly)
- [ ] Rate limiting (per IP: 10 req/min, per user: daily limits)
- [ ] API key rotation capability

**Phase 5-7 (Advanced Security):**
- [ ] SQL injection prevention (parameterized queries)
- [ ] Content Security Policy headers
- [ ] HTTPS enforcement (production)
- [ ] Audit logging (all security events)
- [ ] Error handling (no sensitive info disclosure)

### Critical Security Patterns

```python
# Secure API Key Management
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable required")

# Secure File Upload
from werkzeug.utils import secure_filename
import magic

def validate_upload(file):
    if file.filename == '':
        raise ValueError("No file selected")
    
    filename = secure_filename(file.filename)
    if len(filename) > 255:
        raise ValueError("Filename too long")
    
    # Check file size (25MB limit)
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset
    
    if size > 25 * 1024 * 1024:
        raise ValueError("File too large (25MB limit)")
    
    # Validate file type
    mime_type = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)
    
    allowed_types = ['text/plain', 'message/rfc822', 'application/octet-stream']
    if mime_type not in allowed_types:
        raise ValueError("Invalid file type")
    
    return filename
```

---

## 🤖 AI Integration Specifications

### OpenAI GPT-4o-mini Implementation

**Cost Management:**
- Estimated cost: $0.15/1M input tokens (~$5/month for 1K emails/day)
- Rate limiting: 10 requests/minute per user
- Daily spending caps: $5 for free tier users

**Prompt Engineering Template:**

```python
PHISHING_ANALYSIS_PROMPT = """
You are an expert cybersecurity analyst specializing in phishing detection.

Analyze this email step-by-step:
1. Examine sender authentication (SPF, DKIM, DMARC results)
2. Identify psychological manipulation tactics (urgency, fear, authority)
3. Check URL patterns for typosquatting, shorteners, suspicious domains
4. Assess content for social engineering indicators
5. Review technical headers for routing anomalies

Email to analyze:
{email_content}

Provide your analysis in this exact JSON format:
{{
  "risk_score": <integer 0-100>,
  "classification": "<legitimate|suspicious|phishing>",
  "confidence": <float 0.0-1.0>,
  "evidence": {{
    "sender_auth": "<analysis>",
    "psychological_tactics": ["<tactic1>", "<tactic2>"],
    "url_analysis": "<findings>",
    "header_anomalies": "<findings>",
    "social_engineering": "<analysis>"
  }},
  "recommendation": "<detailed action recommendation>"
}}
"""

# Usage with error handling
async def analyze_with_ai(email_content: str) -> dict:
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PHISHING_ANALYSIS_PROMPT},
                {"role": "user", "content": email_content}
            ],
            max_tokens=1000,
            temperature=0.1  # Low temperature for consistent results
        )
        
        result = json.loads(response.choices[0].message.content)
        validate_ai_response(result)  # Schema validation
        return result
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON response from AI model")
        return fallback_analysis(email_content)
    except Exception as e:
        logger.error(f"AI analysis failed: {str(e)}")
        return fallback_analysis(email_content)
```

### DistilBERT Local Model Implementation

**Model Specifications:**
- Model: `distilbert-base-uncased`
- Fine-tuning dataset: PhishTank + Enron + custom samples
- Expected accuracy: 98.83%
- Inference time: <100ms per email

**Implementation Pattern:**

```python
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch

class PhishingClassifier:
    def __init__(self, model_path: str):
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_path)
        self.model = DistilBertForSequenceClassification.from_pretrained(model_path)
        self.model.eval()
    
    def predict(self, email_text: str) -> dict:
        # Tokenize input
        inputs = self.tokenizer(
            email_text,
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors="pt"
        )
        
        # Get prediction
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        confidence = float(torch.max(predictions))
        prediction = int(torch.argmax(predictions))
        
        return {
            "classification": "phishing" if prediction == 1 else "legitimate",
            "confidence": confidence,
            "model": "distilbert-phishing-v1.0"
        }
```

---

## 🛢️ Database Design

### SQLite Schema (MVP)

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    api_key VARCHAR(64) UNIQUE,
    daily_usage INTEGER DEFAULT 0,
    daily_limit INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Email analysis results
CREATE TABLE email_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    email_hash VARCHAR(64) NOT NULL,  -- SHA-256 of email content
    filename VARCHAR(255),
    file_size INTEGER,
    analysis_result JSON,  -- Store full analysis results
    risk_score INTEGER,
    classification VARCHAR(20),
    confidence FLOAT,
    processing_time FLOAT,  -- milliseconds
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- URL analysis cache
CREATE TABLE url_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 of URL
    url TEXT NOT NULL,
    safe_browsing_result JSON,
    urlvoid_result JSON,
    risk_score INTEGER,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP  -- Cache expiration
);

-- System metrics
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    total_analyses INTEGER DEFAULT 0,
    phishing_detected INTEGER DEFAULT 0,
    accuracy_rate FLOAT,
    avg_processing_time FLOAT,
    api_costs FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### PostgreSQL Migration (Production)

```python
# Alembic migration example
def upgrade():
    # Add indexes for performance
    op.create_index('ix_email_analyses_created_at', 'email_analyses', ['created_at'])
    op.create_index('ix_email_analyses_user_id', 'email_analyses', ['user_id'])
    op.create_index('ix_url_analyses_url_hash', 'url_analyses', ['url_hash'])
    
    # Add partitioning for email_analyses (monthly partitions)
    op.execute("""
        SELECT create_monthly_partitions('email_analyses', 'created_at', 
               DATE_TRUNC('month', CURRENT_DATE), 
               DATE_TRUNC('month', CURRENT_DATE + INTERVAL '12 months'));
    """)
```

---

## 📊 Performance Monitoring

### Key Metrics to Track

**Accuracy Metrics:**
- True Positive Rate (Phishing correctly identified)
- False Positive Rate (Legitimate emails flagged as phishing)
- F1 Score (Balanced accuracy measure)
- Precision and Recall by classification type

**Performance Metrics:**
- Average analysis time per email
- API response times (OpenAI, Safe Browsing, URLVoid)
- Database query performance
- Memory usage during model inference

**Business Metrics:**
- Daily active users
- Email analysis volume
- API costs per analysis
- User retention rates

### Monitoring Implementation

```python
import time
import logging
from functools import wraps

def monitor_performance(func_name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration = (time.time() - start_time) * 1000  # milliseconds
                
                # Log performance metrics
                logging.info(f"Performance: {func_name}", extra={
                    'function': func_name,
                    'duration_ms': duration,
                    'success': success,
                    'error': error
                })
                
                # Store in database for analytics
                store_performance_metric(func_name, duration, success, error)
            
            return result
        return wrapper
    return decorator

# Usage
@monitor_performance("email_analysis")
def analyze_email(email_content: str) -> dict:
    # Analysis implementation
    pass
```

---

## 🚀 Deployment Configuration

### Railway Configuration

**railway.toml:**
```toml
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "always"

[env]
NODE_ENV = "production"
PYTHONPATH = "/app"
```

**Environment Variables Required:**
```bash
# API Keys
OPENAI_API_KEY=sk-...
GOOGLE_SAFE_BROWSING_KEY=AIza...
URLVOID_API_KEY=...

# Database
DATABASE_URL=postgresql://...  # Production
SQLITE_PATH=/app/data/phishing_detector.db  # Development

# Security
SECRET_KEY=...  # Flask secret key
JWT_SECRET_KEY=...  # JWT signing key
BCRYPT_ROUNDS=12

# Rate Limiting
REDIS_URL=redis://...
RATE_LIMIT_PER_MINUTE=10
DAILY_ANALYSIS_LIMIT=100

# Cost Controls
MAX_DAILY_API_COST=5.00
OPENAI_COST_PER_TOKEN=0.00000015
```

### Docker Configuration

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

---

## 📝 Documentation Templates

### README Template (BLUF Format)

```markdown
# AI-Powered Phishing Email Detection System

## 🎯 Bottom Line Up Front
**94.3% accuracy** phishing detection using ensemble AI models (GPT-4o-mini + DistilBERT). 
**Live demo**: [https://phishing-detector.railway.app](url)

**Key Achievement**: Built production-ready cybersecurity application demonstrating AI/ML engineering, secure development practices, and end-to-end system design.

## 🚀 Quick Demo
1. Visit live demo link above
2. Upload sample phishing email from `/demo-emails/` folder
3. View real-time AI analysis with risk scoring and evidence breakdown

## 🏗️ Technical Architecture
[Architecture diagram and component descriptions]

## 🔒 Security Features
[Security implementation highlights]

## 📊 Performance Metrics
[Accuracy, speed, and cost metrics with visualizations]

## 🛠️ Local Development
[Setup and run instructions]
```

### Phase Completion Template

```markdown
# Phase X Completion Report

## ✅ Deliverables Completed
- [ ] Feature 1: Description and verification method
- [ ] Feature 2: Description and verification method
- [ ] Security checklist: OWASP items addressed
- [ ] Tests: Coverage percentage and test results
- [ ] Documentation: Updated sections

## 📊 Performance Results
- Accuracy: X.X% (target: Y.Y%)
- Processing time: Xms (target: <Yms)
- Cost per analysis: $X.XX

## 🔒 Security Verification
- [ ] OWASP item 1: Implementation details
- [ ] OWASP item 2: Implementation details

## 🐛 Issues & Resolutions
1. Issue description → Solution implemented

## ⭐ Demo Ready Features
- Live URL: [https://...]
- Test cases: Available in `/demo-emails/`
- Performance benchmarks: [Link to results]

## 🔄 Next Phase Prep
- Dependencies installed: [List]
- Configuration ready: [Details]
```

---

## 🧪 Testing Strategy

### Test Structure
```
tests/
├── unit/
│   ├── test_email_parser.py
│   ├── test_ai_analysis.py
│   ├── test_url_scanner.py
│   └── test_security.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_database.py
│   └── test_external_apis.py
├── performance/
│   ├── test_load.py
│   └── test_accuracy.py
└── fixtures/
    ├── sample_phishing_emails/
    └── sample_legitimate_emails/
```

### Critical Test Cases

```python
# Security Testing
def test_file_upload_security():
    """Test file upload validates size, type, and sanitizes filename"""
    # Test oversized file rejection
    # Test malicious filename handling
    # Test file type validation
    pass

def test_sql_injection_prevention():
    """Test all database queries prevent SQL injection"""
    # Test parameterized queries
    # Test input sanitization
    pass

# AI Model Testing
def test_phishing_detection_accuracy():
    """Test model accuracy against known dataset"""
    # Load test dataset
    # Run predictions
    # Calculate accuracy metrics
    # Assert >90% accuracy requirement
    pass

def test_api_rate_limiting():
    """Test API cost controls and rate limiting"""
    # Test per-user rate limits
    # Test daily spending caps
    # Test graceful degradation
    pass
```

---

## 💰 Cost Analysis & Optimization

### Expected Costs by Phase

**Phase 1-3 (MVP):**
- Railway hosting: $5/month
- OpenAI API: $5-20/month (depending on usage)
- Domain (optional): $12/year
- **Total**: ~$10-25/month

**Phase 4-7 (Production):**
- Railway Pro: $20/month (database + compute)
- Redis cache: $10/month
- External APIs: $10-30/month
- **Total**: ~$40-60/month

### Cost Optimization Strategies

1. **API Caching**: Cache OpenAI responses for identical emails (SHA-256 hash)
2. **Smart Fallbacks**: Use rule-based detection when API limits hit
3. **Batch Processing**: Group API calls to reduce overhead
4. **Local Models**: Transition to self-hosted DistilBERT for high-volume

---

## 🎯 Phase-by-Phase Success Criteria

### Phase 1: Foundation (Week 1)
**Success Criteria:**
- [ ] Flask app deployed and accessible via Railway URL
- [ ] File upload form accepts .eml, .msg, .txt files
- [ ] Basic email parsing extracts headers and content
- [ ] SQLite database stores analysis results
- [ ] Environment variables secure API keys
- [ ] Git repository with clear initial commit

### Phase 2: MVP Core (Weeks 2-3)
**Success Criteria:**
- [ ] Rule-based detection identifies obvious phishing indicators
- [ ] Web interface displays risk scores and evidence
- [ ] Input validation prevents malicious file uploads
- [ ] Error handling provides user-friendly messages
- [ ] Basic logging captures system events
- [ ] >85% accuracy on sample phishing dataset

### Phase 3: AI Integration (Weeks 4-5)
**Success Criteria:**
- [ ] OpenAI GPT-4o-mini integration with structured prompts
- [ ] JSON schema validation for AI responses
- [ ] Rate limiting prevents API abuse
- [ ] Cost tracking monitors daily spending
- [ ] Fallback analysis when AI unavailable
- [ ] >90% accuracy on expanded test dataset

### Phase 4-7: Production Features
**Success Criteria:**
- [ ] Local DistilBERT model deployment
- [ ] URL scanning with threat intelligence
- [ ] User authentication and session management
- [ ] PostgreSQL migration with performance optimization
- [ ] Comprehensive monitoring and alerting
- [ ] >95% accuracy with <100ms response time

---

This implementation reference provides all the technical specifications, security guidelines, and success criteria needed for phase-by-phase development. Each section can be referenced during development to ensure consistent, secure, and professional implementation.