# 🛡️ AI-Powered Phishing Detection System

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/Rblea97/Phishing_Email_analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/Rblea97/Phishing_Email_analyzer/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/Coverage-83%25-yellow)](docs/evaluation.md)
[![Security](https://img.shields.io/badge/Security-First-red)](docs/SECURITY.md)
[![Release](https://img.shields.io/badge/Release-v1.0.1-green)](https://github.com/Rblea97/Phishing_Email_analyzer/releases)

> **Advanced cybersecurity tool combining rule-based detection with AI analysis to identify phishing emails with high accuracy and detailed evidence reporting.**

## 🎯 Overview

This project demonstrates sophisticated phishing detection capabilities using a dual-analysis approach:
- **Rule-Based Engine**: 9 weighted detection rules with evidence collection
- **AI Analysis**: GPT-4o-mini integration with structured cybersecurity prompts
- **Professional Interface**: Bootstrap-powered dashboard with tabbed results
- **Production Ready**: Rate limiting, cost monitoring, and comprehensive security

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

## 🏆 Project Highlights

This project demonstrates:
- **AI/ML Integration**: Production-ready OpenAI GPT integration
- **Cybersecurity Expertise**: Advanced threat detection and analysis
- **Full-Stack Development**: Complete web application with professional UI
- **Security-First Design**: Comprehensive security controls and monitoring
- **Production Readiness**: Deployment configuration, testing, documentation
- **Cost Optimization**: Efficient AI usage with monitoring and controls

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

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Rblea97/Phishing_Email_analyzer/issues)
- **Documentation**: [Complete Documentation](docs/) - All claims backed by detailed analysis
- **Security**: [Security Policy](docs/SECURITY.md) - Comprehensive security implementation
- **Privacy**: [Privacy Compliance](docs/privacy-compliance.md) - GDPR/CCPA compliance documentation

---

*Built with ❤️ using Flask, OpenAI GPT-4o-mini, and security-first development practices*