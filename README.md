# AI-Powered Phishing Email Detection System

## 🎯 Bottom Line Up Front

**Dual-analysis phishing detection** combining rule-based analysis with GPT-4o-mini AI integration, achieving comprehensive threat assessment with professional tabbed interface.

**Live Demo**: Production-ready Flask application with AI integration
**AI Enhanced**: OpenAI GPT-4o-mini provides structured analysis alongside 9 weighted detection rules

**Key Achievement**: Complete Phase 3 MVP with dual detection engines (rules + AI), cost monitoring, rate limiting, and evidence-based scoring demonstrating advanced cybersecurity and AI integration skills.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Virtual environment (recommended)
- OpenAI API key (for AI features)
- Git

### Local Development Setup (Phase 3 - AI Integration)

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd Phising_Email_analyzer
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Add your OpenAI API key:
   echo "OPENAI_API_KEY=your-api-key-here" >> .env
   echo "SECRET_KEY=your-secret-key-here" >> .env
   ```

4. **Initialize Database**
   ```bash
   python init_db.py
   python migrate_to_phase2.py
   python migrate_to_phase3.py
   ```

5. **Run Application**
   ```bash
   python app_phase2.py
   # Visit: http://localhost:5000
   ```

6. **Run Tests**
   ```bash
   python run_tests.py
   python -m pytest tests/test_ai.py  # AI-specific tests
   ```

### Railway Deployment (Phase 3)

1. **Connect Repository**
   - Connect your GitHub repository to Railway
   - Railway will automatically detect the Python app

2. **Set Environment Variables**
   ```
   SECRET_KEY=your-production-secret-key
   OPENAI_API_KEY=your-openai-api-key
   FLASK_ENV=production
   PORT=5000
   ```

3. **Deploy**
   - Railway automatically builds and deploys
   - Health check endpoint: `/health`
   - AI status included in health checks

---

## 🏗️ Technical Architecture

### Phase 3 AI Integration

```
┌─────────────────────────────────────────────────────────────┐
│           Flask Web Application (Phase 3)                  │
│  Upload → Parse → [Rule Analysis + AI Analysis] → Display  │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                Email Parser Module                          │
│    MIME Parsing | HTML→Text | URL Extraction | Security    │
└─────────────┬───────────────────────────┬───────────────────┘
              │                           │
┌─────────────▼───────────────┐ ┌─────────▼───────────────────┐
│    Rule-Based Detection     │ │      AI Analysis Engine     │
│  9 Weighted Rules | Evidence│ │   GPT-4o-mini | Structured  │
│  Collection | Risk Scoring  │ │   Prompts | JSON Validation │
└─────────────┬───────────────┘ └─────────┬───────────────────┘
              │                           │
              └───────────┬───────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              SQLite Database (Phase 3)                     │
│  emails | email_parsed | detections | ai_detections |      │
│           ai_usage_stats | rate_limiting                   │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack (Phase 3)
- **Backend**: Flask 3.0.0, Python 3.9+
- **AI Integration**: OpenAI GPT-4o-mini API, structured prompts
- **Email Processing**: Python email library, html2text, email-validator
- **Database**: SQLite (Phase 3 schema) → PostgreSQL (Phase 6)
- **Security**: Rate limiting (Flask-Limiter), JSON schema validation, cost monitoring
- **Deployment**: Railway, Gunicorn, environment-based API key management
- **Frontend**: Bootstrap 5 with tabbed analysis interface
- **Testing**: Pytest with mocked AI calls, 90%+ coverage

---

## 🔒 Security Features

### Implemented (Phase 3)
- ✅ **Secure File Upload**: Size limits (25MB), type validation (.eml, .txt, .msg)
- ✅ **Input Sanitization**: Werkzeug secure_filename, MIME type detection, HTML stripping
- ✅ **Email Parsing Security**: Size limits (1MB parsed text), timeout protection (30s)
- ✅ **AI Security**: 4K token input limit, no binary content to AI, response validation
- ✅ **Rate Limiting**: 10 AI requests per minute per IP with 429 responses
- ✅ **Cost Monitoring**: Token usage tracking, daily spending alerts
- ✅ **API Key Security**: Environment variables only, no hardcoded keys
- ✅ **JSON Schema Validation**: Strict AI response validation prevents injection
- ✅ **Error Handling**: Graceful AI failures, comprehensive logging
- ✅ **Database Security**: Parameterized queries, SQL injection prevention

### AI-Specific Security
- **Input Sanitization**: Only text+metadata sent to AI (no binary data)
- **Token Limits**: 4K input tokens max, automatic truncation
- **Response Validation**: JSON schema enforcement for all AI responses
- **Timeout Protection**: 10s AI request timeout with 2 retry attempts
- **Cost Controls**: Daily usage tracking, estimated cost per analysis

---

## 📊 Features & Functionality

### Phase 3: AI Integration Complete (✅ IMPLEMENTED)

#### Dual Analysis Engine
- **Rule-Based Detection**: 9 weighted rules with evidence collection
- **AI Analysis**: GPT-4o-mini structured analysis with cybersecurity prompts
- **Tabbed Interface**: Professional Bootstrap tabs showing both analysis types
- **Cost Transparency**: Token usage and cost estimation displayed per analysis

#### AI Integration Features
- **Structured Prompts**: Cybersecurity-focused analysis instructions
- **JSON Validation**: Schema-enforced responses prevent injection attacks
- **Evidence Correlation**: AI evidence mapped to rule-based patterns
- **Performance Monitoring**: AI request timing and success rates
- **Graceful Degradation**: Rule-based analysis continues if AI fails

#### Enhanced UI (Phase 3)
- **Tabbed Analysis**: Rule-Based Detection | AI Analysis
- **AI Status Indicators**: Success/failure badges, processing time
- **Cost Display**: Token usage and estimated cost per analysis
- **Comparison View**: Side-by-side rule vs AI risk assessment
- **Enhanced Statistics**: AI usage metrics and daily cost tracking

### Phase 3 Detection Capabilities:

#### Rule-Based Engine (9 Rules):
1. **Header Mismatch** (15 pts): Display name domain ≠ From domain
2. **Reply-To Mismatch** (10 pts): Reply-To domain ≠ From domain  
3. **Auth Failures** (20 pts): SPF/DKIM/DMARC failure indicators
4. **Urgent Language** (10 pts): "expires today", "immediate action" patterns
5. **URL Shorteners** (10 pts): bit.ly, t.co, tinyurl detection
6. **Suspicious TLDs** (10 pts): .top, .xyz, .click domains
7. **Unicode Spoofing** (10 pts): Non-ASCII or mixed script domains
8. **Generic Greetings** (5 pts): "Dear customer", "valued user"
9. **Attachment Keywords** (5 pts): "invoice" + "payment" + links present

#### AI Analysis Engine:
- **Authentication Analysis**: SPF/DKIM/DMARC evaluation with context
- **Content Pattern Recognition**: Advanced phishing tactic identification
- **URL Risk Assessment**: Domain reputation and suspicious patterns
- **Social Engineering Detection**: Psychological manipulation indicators
- **Structured Evidence**: Categorized findings with confidence scoring

### Phase 4-7: Roadmap 📋
- **Advanced AI Models**: Local model deployment and fine-tuning
- **Real-time URL Scanning**: Safe Browsing API integration
- **User Authentication**: Multi-user support with role-based access
- **Advanced Analytics**: Reporting dashboard with trend analysis
- **Enterprise Features**: PostgreSQL, Redis caching, monitoring

---

## 🧠 AI Integration Details

### GPT-4o-mini Implementation

**Model Configuration**:
- **Model**: GPT-4o-mini (cost-optimized)
- **Input Limit**: 4,000 tokens (auto-truncated)
- **Output Limit**: 1,000 tokens
- **Timeout**: 10 seconds with 2 retry attempts
- **Temperature**: 0.1 (consistent analysis)

**Structured Prompt Template**:
```
You are a cybersecurity analyst. Analyze this email step-by-step:
1. Examine sender authentication (SPF, DKIM, DMARC).
2. Identify manipulation tactics in the content.
3. Check URLs for suspicious domains or patterns.
4. Evaluate for phishing indicators.

Return JSON: {
  "score": <0-100>,
  "label": "Likely Safe" | "Suspicious" | "Likely Phishing",
  "evidence": [
    {"id": "RULE_ID", "description": "Text explanation", "weight": <int>}
  ]
}
```

### Cost Estimation (Phase 3)
- **GPT-4o-mini Pricing**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Average Cost**: $0.001-0.005 per email analysis
- **Monthly Estimate**: ~$5 for 1,000 emails/day
- **Cost Tracking**: Real-time token usage and cost estimation

### Rate Limiting
- **Per-IP Limits**: 10 AI requests per minute
- **Global Limits**: 100 requests per hour (adjustable)
- **Error Handling**: 429 status codes with retry-after headers
- **Fallback**: Rule-based analysis continues during rate limiting

---

## 📁 Project Structure (Phase 3)

```
Phishing_Email_analyzer/
├── app_phase2.py          # Main Flask application (Phase 3)
├── init_db.py            # Database initialization
├── requirements.txt       # Python dependencies (includes AI)
├── run_tests.py          # Test runner with coverage reporting
├── Procfile              # Railway deployment config
├── railway.toml          # Railway settings
├── .env.example          # Environment template (includes OpenAI)
├── .gitignore            # Git ignore rules
│
├── services/             # Phase 3 service modules
│   ├── __init__.py       # Package initialization
│   ├── parser.py         # Email parsing module
│   ├── rules.py          # Rule-based detection engine
│   ├── ai.py             # GPT-4o-mini integration
│   └── schema.py         # JSON validation for AI responses
│
├── templates/            # HTML templates (Phase 3 UI)
│   ├── base.html         # Base template with Bootstrap
│   ├── upload.html       # Upload interface
│   ├── analysis.html     # Tabbed analysis results (Phase 3)
│   ├── analyses.html     # Analysis history
│   ├── stats.html        # Enhanced statistics with AI metrics
│   └── error.html        # Error pages
│
├── tests/                # Comprehensive test suite
│   ├── fixtures/         # Realistic email samples (5 test files)
│   ├── conftest.py       # Pytest configuration
│   ├── test_parser.py    # Parser unit tests
│   ├── test_rules.py     # Rule engine tests
│   ├── test_ai.py        # AI integration tests (mocked)
│   └── test_integration.py # End-to-end tests
│
└── README.md             # Complete documentation
```

---

## 🛠️ Development Guide

### Phase 3 Database Schema

**Core Tables** (Phase 2):
```sql
-- Email metadata
CREATE TABLE emails (
    id INTEGER PRIMARY KEY,
    filename TEXT,
    size_bytes INTEGER,
    sha256 TEXT,
    parse_summary_json TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Parsed email content
CREATE TABLE email_parsed (
    id INTEGER PRIMARY KEY,
    email_id INTEGER,
    headers_json TEXT,
    text_body TEXT,
    html_body TEXT,
    html_as_text TEXT,
    urls_json TEXT,
    parse_time_ms REAL,
    security_warnings TEXT,
    FOREIGN KEY (email_id) REFERENCES emails (id)
);

-- Rule-based detection results
CREATE TABLE detections (
    id INTEGER PRIMARY KEY,
    email_id INTEGER,
    score INTEGER,
    label TEXT,
    confidence REAL,
    evidence_json TEXT,
    processing_time_ms REAL,
    rules_checked INTEGER,
    rules_fired INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails (id)
);
```

**AI Integration Tables** (Phase 3):
```sql
-- AI analysis results
CREATE TABLE ai_detections (
    id INTEGER PRIMARY KEY,
    email_id INTEGER,
    score INTEGER CHECK (score >= 0 AND score <= 100),
    label TEXT CHECK (label IN ('Likely Safe', 'Suspicious', 'Likely Phishing')),
    evidence_json TEXT,
    tokens_used INTEGER,
    cost_estimate REAL,
    processing_time_ms REAL,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails (id)
);

-- Daily AI usage statistics
CREATE TABLE ai_usage_stats (
    id INTEGER PRIMARY KEY,
    date DATE UNIQUE,
    requests_count INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    avg_processing_time_ms REAL,
    success_rate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints (Phase 3)

| Endpoint | Method | Purpose | Rate Limit |
|----------|--------|---------|------------|
| `/` | GET | Main upload interface | None |
| `/upload` | POST | Handle file uploads (dual analysis) | 10/min |
| `/analysis/<id>` | GET | View analysis results (tabbed) | None |
| `/analyses` | GET | Analysis history | None |
| `/stats` | GET | System statistics (includes AI) | None |
| `/health` | GET | Health check (includes AI status) | None |

### Environment Variables (Phase 3)

```bash
# Required
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key

# Optional
FLASK_ENV=development
PORT=5000
DATABASE_PATH=phishing_detector.db
```

### AI Service Usage

```python
from services.ai import analyze_email_with_ai

# Analyze email with AI
result = analyze_email_with_ai(parsed_email)

if result.success:
    print(f"AI Score: {result.score}")
    print(f"AI Label: {result.label}")
    print(f"Tokens Used: {result.tokens_used}")
    print(f"Cost: ${result.cost_estimate:.4f}")
else:
    print(f"AI Failed: {result.error_message}")
```

---

## 🧪 Testing (Phase 3)

### Test Suite Overview
- **Parser Tests**: Email parsing with realistic fixtures
- **Rule Engine Tests**: Individual rule validation and integration
- **AI Integration Tests**: Mocked OpenAI calls, schema validation
- **End-to-End Tests**: Complete analysis pipeline
- **Security Tests**: Input validation, rate limiting

### Running Tests

```bash
# All tests
python run_tests.py

# Specific test suites
python -m pytest tests/test_parser.py -v
python -m pytest tests/test_rules.py -v
python -m pytest tests/test_ai.py -v        # Mocked AI tests
python -m pytest tests/test_integration.py -v

# Coverage report
python -m pytest --cov=services --cov-report=html
```

### Test Fixtures (5 Realistic Emails)
1. **safe_newsletter.eml**: Legitimate marketing email
2. **obvious_phishing.eml**: Clear phishing attempt
3. **spoofed_display.eml**: Display name spoofing
4. **auth_failure.eml**: Authentication failure indicators
5. **unicode_spoof.eml**: Unicode domain spoofing

### AI Testing Strategy
- **Mocked Responses**: No actual OpenAI API calls during testing
- **Schema Validation**: Ensures JSON response structure
- **Error Handling**: Tests timeout, rate limiting, API failures
- **Cost Calculation**: Validates token usage and cost estimation

---

## 📈 Performance & Monitoring (Phase 3)

### Performance Metrics
- **Rule Analysis**: <500ms per email
- **AI Analysis**: <2000ms per email (including API call)
- **Combined Analysis**: <2500ms total processing time
- **Database**: Indexed queries with <100ms response times
- **Rate Limiting**: 10 AI requests/minute per IP

### Cost Monitoring
- **Daily Tracking**: Token usage and estimated costs
- **Per-Analysis**: Individual cost breakdown
- **Monthly Projections**: Based on usage patterns
- **Cost Alerts**: Configurable spending thresholds

### Health Check Response (Phase 3)
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "database": {
    "emails": 150,
    "ai_analyses": 145,
    "missing_tables": []
  },
  "services": {
    "parser": "ok",
    "rules": "ok",
    "rules_count": 9,
    "ai": {
      "status": "ok",
      "daily_tokens": 15420,
      "daily_cost": 0.0231
    }
  }
}
```

---

## 🚦 Deployment Status

### Phase 3 Deliverables ✅

| Component | Status | Details |
|-----------|--------|---------|
| AI Integration | ✅ Complete | GPT-4o-mini with structured prompts |
| Dual Analysis | ✅ Complete | Rule + AI engines in parallel |
| Tabbed Interface | ✅ Complete | Professional Bootstrap tabs |
| Rate Limiting | ✅ Complete | Flask-Limiter with IP-based limits |
| Cost Monitoring | ✅ Complete | Token tracking and cost estimation |
| Schema Validation | ✅ Complete | JSON validation for AI responses |
| Database Migration | ✅ Complete | Phase 3 schema with AI tables |
| Security Controls | ✅ Complete | API key management, input sanitization |
| Test Suite | ✅ Complete | Mocked AI tests, full coverage |
| Documentation | ✅ Complete | Updated README with AI details |

### Deployment Readiness
- **Railway Compatible**: Procfile and environment configuration ready
- **Environment Variables**: Secure API key management
- **Health Monitoring**: AI service status in health checks
- **Error Handling**: Graceful AI failures with rule-based fallback
- **Cost Control**: Rate limiting and usage monitoring

### Next Phase Preview 🔮

**Phase 4 Goals**:
- Real-time URL scanning integration
- Advanced threat intelligence feeds
- Enhanced AI prompt engineering
- Performance optimizations

**Estimated Timeline**: 3-4 weeks

---

## 🤝 Contributing

### Development Workflow (Phase 3)
1. Create feature branch: `git checkout -b feature/enhanced-ai`
2. Set up environment: Add `OPENAI_API_KEY` to .env
3. Run migrations: `python migrate_to_phase3.py`
4. Implement changes with tests (mock AI calls)
5. Update documentation
6. Submit pull request

### AI Development Guidelines
- **Mock API Calls**: Always use mocked responses in tests
- **Cost Awareness**: Monitor token usage in development
- **Schema Compliance**: Validate all AI responses
- **Error Handling**: Plan for API failures and rate limits
- **Security First**: Never log API keys or sensitive data

### Commit Message Format
```
type(scope): brief description

feat(ai): add structured prompt engineering
fix(rate-limit): resolve IP-based limiting issue
docs(readme): update Phase 3 documentation
test(ai): add mocked response validation
```

---

## 💰 Cost Analysis (Phase 3)

### GPT-4o-mini Cost Breakdown
- **Input Tokens**: $0.15 per 1M tokens
- **Output Tokens**: $0.60 per 1M tokens
- **Average Email**: ~500 input + ~200 output tokens
- **Cost Per Analysis**: ~$0.0015
- **Monthly (1K emails/day)**: ~$45

### Cost Optimization
- **Token Limits**: 4K input token cap with truncation
- **Efficient Prompts**: Structured prompts minimize token usage
- **Caching Strategy**: Prevent duplicate analyses (by hash)
- **Rate Limiting**: Controls spending velocity
- **Usage Monitoring**: Daily tracking with alerts

---

## 📄 License & Security

### Security Policy (Phase 3)
- **API Key Management**: Environment variables only, never logged
- **Input Validation**: 4K token limit, no binary content to AI
- **Response Validation**: JSON schema enforcement
- **Rate Limiting**: Prevents API abuse and cost overruns
- **Error Handling**: No sensitive information disclosure
- **Audit Trail**: All analyses logged with cost tracking

### AI Ethics & Compliance
- **No PII to AI**: Only email metadata and sanitized content
- **Transparent Costs**: Clear cost display to users
- **Graceful Degradation**: Rule-based fallback always available
- **Data Retention**: Standard email analysis retention policies

---

## 📞 Support & Contact

**Project Purpose**: Advanced cybersecurity portfolio demonstrating AI integration with security-first development

**Technologies Demonstrated**:
- AI/ML integration (OpenAI GPT-4o-mini)
- Dual detection engines (rules + AI)
- Cost monitoring and optimization
- Rate limiting and security controls
- Professional tabbed interface design
- Comprehensive testing with mocked services
- Production-ready deployment practices

**Phase 3 Achievements**:
- ✅ GPT-4o-mini integration with structured cybersecurity prompts
- ✅ Dual analysis pipeline with tabbed results display
- ✅ Comprehensive rate limiting and cost monitoring
- ✅ JSON schema validation for AI response security
- ✅ Professional UI with cost transparency
- ✅ Production-ready deployment configuration

**Live Demo**: Ready for Railway deployment with AI integration

---

*Built with ❤️ using Flask, OpenAI GPT-4o-mini, and security-first AI integration practices*

**Phase 3 AI Integration Complete** ✅ | **Ready for Production Deployment** 🚀 | **Cost Optimized** 💰