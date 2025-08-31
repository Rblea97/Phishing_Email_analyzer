# 🛡️ AI-Powered Phishing Detection System
## 🎓 Computer Science Portfolio Project by Richard Blea

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/Rblea97/Phishing_Email_analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/Rblea97/Phishing_Email_analyzer/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/Coverage-83%25-yellow)](docs/evaluation.md)
[![Security](https://img.shields.io/badge/Security-First-red)](docs/SECURITY.md)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Richard%20Blea-blue)](https://www.linkedin.com/in/richard-blea-748914159)

> **Academic capstone project demonstrating advanced cybersecurity, AI/ML integration, and full-stack development skills. Built as a comprehensive phishing detection system combining rule-based analysis with OpenAI GPT-4o-mini for intelligent threat assessment.**

### 👨‍💻 About the Developer
**Richard Blea** | CU Denver Computer Science Student | Cybersecurity Professional in Training  
📧 [rblea97@gmail.com](mailto:rblea97@gmail.com) | 💼 [LinkedIn](https://www.linkedin.com/in/richard-blea-748914159) | 📍 Denver, CO | 🎓 Graduating Spring 2026  
**Seeking entry-level cybersecurity positions: SOC Analyst, Information Security Analyst**

## 🎯 Project Overview

This personal cybersecurity project showcases advanced computer science skills through a sophisticated phishing detection system. Developed during Fall 2025 semester and inspired by coursework in mobile security at CU Denver, it demonstrates my ability to integrate modern AI technologies with traditional cybersecurity approaches.

### 🎓 Skills Development Focus
- **Threat Detection & Analysis**: Email security protocols, phishing pattern recognition, incident response
- **Security Operations**: Rule-based detection engines, log analysis, evidence collection and documentation
- **Network Security**: Email header analysis, SPF/DKIM/DMARC authentication, suspicious domain identification
- **Security Tools & Automation**: Python scripting for security analysis, API integration, automated threat assessment
- **Incident Documentation**: Detailed evidence reporting, risk scoring methodologies, security documentation practices

### 🔧 Technical Implementation
- **Rule-Based Engine**: 9 weighted detection rules with evidence collection
- **AI Analysis**: GPT-4o-mini integration with structured cybersecurity prompts
- **Professional Interface**: Bootstrap-powered dashboard with tabbed results
- **Enterprise Features**: Rate limiting, cost monitoring, and comprehensive security

## 🎬 Live Demo

### Animated Demo Preview
![Phishing Detection Demo](demo.gif)

*Live demonstration: Upload → Analysis → Results*

**What you'll see in the demo:**
- Upload a phishing email sample
- Dual analysis (Rule-based + AI) processing 
- Detailed threat scoring and evidence
- Professional results dashboard
- Analysis history tracking

## 📸 Screenshots

### Main Dashboard
![Dashboard](docs/screenshots/homepage.png)

### File Upload Interface  
![Upload Interface](docs/screenshots/upload-interface.png)

### Analysis Results Overview
![Analysis Results](docs/screenshots/analysis-overview.png)

### Rule-Based Detection Details
![Rule Analysis](docs/screenshots/rule-based-analysis.png)

### AI Analysis Results
![AI Analysis](docs/screenshots/ai-analysis.png)

<details>
<summary>📱 More Screenshots</summary>

### Analysis History
![History](docs/screenshots/analysis-history.png)

### Mobile Responsive Design
![Mobile](docs/screenshots/mobile-responsive.png)

</details>

## ⚡ Quick Start

### One-Click Development Setup

```bash
# Clone and set up everything
git clone https://github.com/Rblea97/Phishing_Email_analyzer.git
cd Phishing_Email_analyzer
make dev
# Add your OpenAI API key to .env, then:
make run
```

### Docker Setup (Recommended)

```bash
# Build and run with Docker
git clone https://github.com/Rblea97/Phishing_Email_analyzer.git
cd Phishing_Email_analyzer
cp .env.example .env
# Add your OpenAI API key to .env
make docker-build
make docker-run
```

### Manual Installation

<details>
<summary>Click for manual setup instructions</summary>

#### Prerequisites
- Python 3.9+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

#### Installation Steps

```bash
# Clone the repository
git clone https://github.com/Rblea97/Phishing_Email_analyzer.git
cd Phishing_Email_analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key
```

#### Database Setup

```bash
# Initialize database
python init_db.py
python migrate_to_phase2.py
python migrate_to_phase3.py
```

#### Run Application

```bash
python app_phase2.py
# Visit: http://localhost:5000
```

</details>

### Development Commands

```bash
make test      # Run test suite with coverage
make lint      # Code quality and security checks  
make format    # Format code with black/isort
make clean     # Clean temporary files
make build     # Production build with all checks
```

## 🚀 Features

### 🔍 Dual Analysis Engine
- **Rule-Based Detection**: 9 sophisticated rules covering common phishing indicators
- **AI-Powered Analysis**: GPT-4o-mini with cybersecurity-focused prompts
- **Evidence Collection**: Detailed breakdown of detection reasoning
- **Risk Scoring**: 0-100 scoring system with confidence levels

#### 📋 Detection Rules Summary

| Rule ID | Description | Severity (Weight) | Example Detection |
|---------|-------------|-------------------|------------------|
| **HEADER_MISMATCH** | Display name domain differs from From domain | High (25) | "Microsoft Office 365" from `notifications@fake-service123.com` |
| **AUTH_FAIL_HINTS** | SPF/DKIM/DMARC authentication failures | High (30) | `spf=fail smtp.mailfrom=admin@suspicious.com` |
| **REPLYTO_MISMATCH** | Reply-To domain differs from From domain | Medium (10) | From: `bank@legit.com`, Reply-To: `verify@different.net` |
| **URGENT_LANGUAGE** | Contains urgent/pressure language | Medium (10) | "immediate action", "expires today", "suspend account" |
| **URL_SHORTENER** | Contains shortened URLs | Medium (10) | `bit.ly`, `tinyurl.com`, `t.co` links |
| **SUSPICIOUS_TLDS** | Suspicious top-level domains | Medium (10) | `.top`, `.xyz`, `.click` domains |
| **UNICODE_SPOOF** | Unicode spoofing attempts | Medium (10) | Non-ASCII characters in domains |
| **NO_PERSONALIZATION** | Generic greetings without personalization | Low (5) | "Dear Customer", "Valued User" |
| **ATTACHMENT_KEYWORDS** | Attachment mentions with suspicious links | Low (5) | "invoice", "payment" keywords with URLs present |

*See [test fixtures](tests/fixtures/) for real examples of these rules in action.*

### 🛡️ Security Features
- **Secure File Upload**: Type validation, size limits, malware protection
- **Rate Limiting**: API abuse prevention (10 requests/min per IP)
- **Cost Controls**: Token usage monitoring and spending alerts
- **Input Sanitization**: Comprehensive validation and error handling

### 📊 Professional Interface
- **Tabbed Results**: Clean separation of rule-based vs AI analysis
- **Mobile Responsive**: Professional Bootstrap design
- **Analysis History**: Complete audit trail with filtering
- **Statistics Dashboard**: Usage metrics and performance monitoring

### 🔧 Detection Capabilities

#### Rule-Based Engine
- Header authenticity verification
- SPF/DKIM/DMARC authentication checks
- Suspicious URL pattern detection
- Social engineering language analysis
- Unicode spoofing identification
- Generic greeting detection
- Suspicious attachment analysis

#### AI Analysis
- Advanced pattern recognition beyond rules
- Context-aware threat assessment
- Natural language processing for social engineering
- Structured evidence reporting
- Confidence scoring with explanations

## 📈 Performance Metrics
- **Analysis Speed**: ~500ms rule-based, 2-4s with AI analysis ([Benchmark Methodology](docs/benchmarks.md))
- **Test Coverage**: 83% ([Coverage Report](docs/evaluation.md) - authoritative source)
- **Detection Rules**: 9 weighted rules with evidence collection ([Rule Details](docs/rules.md))
- **Cost Efficiency**: ~$0.0002-0.004 per email analysis ([Cost Analysis](docs/cost-analysis.md) - measured usage)
- **Scalability**: Rate-limited for production deployment ([Architecture](docs/architecture.md))

*All metrics are measured and documented with reproducible methodologies. See individual documentation links for detailed analysis.*

## 🛠️ Technology Stack

- **Backend**: Flask 3.0.0, Python 3.9+ ([Architecture](docs/architecture.md))
- **AI Integration**: OpenAI GPT-4o-mini API ([Cost Analysis](docs/cost-analysis.md))
- **Database**: SQLite (development) → PostgreSQL (production) ([Architecture](docs/architecture.md))
- **Frontend**: Bootstrap 5, responsive design ([Architecture](docs/architecture.md))
- **Security**: Flask-Limiter, comprehensive input validation ([Security Policy](docs/SECURITY.md))
- **Testing**: Pytest with 83% coverage ([Test Results](docs/evaluation.md))
- **Deployment**: Railway-ready with Gunicorn ([Architecture](docs/architecture.md))

## 📋 Project Structure

```
Phishing_Email_analyzer/
├── app_phase2.py          # Main Flask application
├── requirements.txt       # Dependencies
├── services/             # Core detection modules
│   ├── parser.py         # Email parsing with security
│   ├── rules.py          # Rule-based detection engine  
│   ├── ai.py             # GPT-4o-mini integration
│   └── schema.py         # AI response validation
├── templates/            # Professional UI templates
├── tests/                # Comprehensive test suite
│   └── fixtures/         # Realistic email samples
├── docs/                 # Documentation and screenshots
└── README.md            # This file
```

## 🔒 Security & Privacy

- **No PII to AI**: Only sanitized metadata sent to external APIs ([Privacy Compliance](docs/privacy-compliance.md))
- **API Key Security**: Environment variables only, never logged ([Security Policy](docs/SECURITY.md))
- **Input Validation**: 4K token limits, JSON schema validation ([Architecture](docs/architecture.md))
- **Rate Limiting**: Prevents abuse and controls costs ([Security Policy](docs/SECURITY.md))
- **Audit Trail**: Complete analysis logging for security review ([Security Policy](docs/SECURITY.md))

**Compliance**: GDPR & CCPA compliant with privacy-by-design architecture ([Privacy Documentation](docs/privacy-compliance.md))

## 📊 Cost Analysis

- **Model**: GPT-4o-mini (cost-optimized) ([Cost Analysis](docs/cost-analysis.md))
- **Average Cost**: $0.0002-0.004 per email (measured production usage)
- **Monthly Estimate**: $6-120 for 1,000 emails/day ([Detailed Projections](docs/cost-analysis.md))
- **Cost Controls**: Token limits, usage monitoring, spending alerts ([Implementation](docs/cost-analysis.md))

*All cost estimates based on measured API usage and documented in [Cost Analysis](docs/cost-analysis.md)*

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Cybersecurity Skills Demonstrated

### 🔍 Security Analysis & Threat Detection
- **Email Security Analysis**: Header parsing, authentication protocol validation (SPF/DKIM/DMARC)
- **Phishing Detection**: Pattern recognition, suspicious URL analysis, social engineering identification
- **Incident Investigation**: Evidence collection, threat scoring, detailed documentation of findings
- **Risk Assessment**: 0-100 scoring methodology, confidence level calculation, threat categorization

### 🛡️ Security Operations Center (SOC) Relevant Skills  
- **Automated Detection**: Rule-based engine development, alert generation, false positive reduction
- **Log Analysis**: Email header examination, authentication results parsing, anomaly detection
- **Threat Intelligence**: Suspicious domain identification, URL shortener analysis, Unicode spoofing detection
- **Response Documentation**: Structured evidence reporting, playbook development, incident tracking

### 🔧 Technical Security Tools
- **Python Security Scripting**: Automated analysis tools, API integration, data parsing
- **Security Testing**: Comprehensive test coverage (83%), vulnerability assessment methodologies
- **Database Security**: Secure data handling, audit trail implementation, privacy protection
- **Deployment Security**: Rate limiting, input validation, secure configuration management

## 📚 Comprehensive Documentation

All claims in this README are backed by detailed documentation with implementation references:

### Core Documentation
- **[Performance Benchmarks](docs/benchmarks.md)** - Detailed performance measurement methodology and results
- **[Cost Analysis](docs/cost-analysis.md)** - Complete financial analysis with measured usage data
- **[System Architecture](docs/architecture.md)** - Comprehensive system design and implementation details
- **[Security Policy](docs/SECURITY.md)** - Security implementation with code references and validation
- **[Privacy Compliance](docs/privacy-compliance.md)** - GDPR/CCPA compliance with PII protection details

### Technical Documentation  
- **[Detection Rules](docs/rules.md)** - Complete rule engine documentation with implementation references
- **[Evaluation Results](docs/evaluation.md)** - Test coverage metrics and accuracy validation
- **[API Reference](docs/API.md)** - Complete API documentation with examples
- **[Installation Guide](docs/INSTALLATION.md)** - Setup and deployment instructions
- **[Threat Model](docs/threat-model.md)** - Security threat analysis and data flow documentation

*All documentation includes implementation references, test validation, and external standard compliance.*

## 🚀 For Security Professionals & Hiring Managers

### 📋 Cybersecurity Portfolio Summary
- **Threat Analysis Expertise**: Multi-layered phishing detection combining rule-based analysis with AI assessment
- **SOC-Ready Skills**: Automated detection, evidence collection, incident documentation, risk scoring
- **Technical Proficiency**: Python security scripting, email security protocols, threat intelligence analysis
- **Quality Assurance**: 83% test coverage, comprehensive documentation, production-ready deployment
- **Education**: CU Denver Computer Science (Spring 2026) + Cybersecurity & Defense Certificate

### 📞 Contact Richard Blea
- **Location**: Denver, CO (willing to relocate)
- **Email**: [rblea97@gmail.com](mailto:rblea97@gmail.com)
- **LinkedIn**: [linkedin.com/in/richard-blea-748914159](https://www.linkedin.com/in/richard-blea-748914159)
- **Target Roles**: SOC Analyst, Information Security Analyst, Cybersecurity Analyst
- **Availability**: Graduating Spring 2026, seeking entry-level cybersecurity positions

### 📚 Technical Documentation
- **[Complete Documentation](docs/)** - All technical implementations with detailed analysis
- **[Security Policy](docs/SECURITY.md)** - Comprehensive security implementation
- **[Architecture](docs/architecture.md)** - System design and scalability considerations
- **[Test Results](docs/evaluation.md)** - Quality assurance and performance metrics

---

*🎓 Academic project showcasing industry-ready development practices and modern technology integration*