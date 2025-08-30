# 🛡️ AI-Powered Phishing Detection System

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/Rblea97/Phishing_Email_analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/Rblea97/Phishing_Email_analyzer/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/Coverage-83%25-yellow)](docs/evaluation.md)
[![Security](https://img.shields.io/badge/Security-First-red)](docs/SECURITY.md)
[![Release](https://img.shields.io/badge/Release-v1.0.0-green)](https://github.com/Rblea97/Phishing_Email_analyzer/releases)

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

## 🧪 Try It Yourself

### Sample Phishing Emails
We've created 8 realistic phishing email samples for testing:

📧 **[Download Sample Files](samples_for_users/)** - Ready-to-test phishing examples

**Available Samples:**
- Corporate HR benefits scam
- PayPal security alert fraud  
- Amazon delivery issue scam
- Microsoft account warning
- Cryptocurrency wallet breach
- IRS tax refund fraud
- Business invoice scam
- Dating site romance scam

### Automated Demo Generation
Generate your own demo video using Playwright automation:

```bash
# Install demo dependencies
python scripts/install_demo_deps.py

# Test the setup
python scripts/test_demo.py

# Generate 60-second demo video
python scripts/generate_demo.py
```

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
- **Analysis Speed**: ~500ms rule-based, 2-4s with AI analysis
- **Test Coverage**: 83% (see [Coverage Report](docs/evaluation.md))
- **Detection Rules**: 9 weighted rules with evidence collection ([Rule Details](docs/rules.md))
- **Cost Efficiency**: ~$0.0002-0.004 per email analysis (based on measured usage)
- **Scalability**: Rate-limited for production deployment

## 🛠️ Technology Stack

- **Backend**: Flask 3.0.0, Python 3.9+
- **AI Integration**: OpenAI GPT-4o-mini API
- **Database**: SQLite (development) → PostgreSQL (production)
- **Frontend**: Bootstrap 5, responsive design
- **Security**: Flask-Limiter, comprehensive input validation
- **Testing**: Pytest with 83% coverage ([Test Results](docs/evaluation.md))
- **Deployment**: Railway-ready with Gunicorn

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

- **No PII to AI**: Only sanitized metadata sent to external APIs
- **API Key Security**: Environment variables only, never logged
- **Input Validation**: 4K token limits, JSON schema validation
- **Rate Limiting**: Prevents abuse and controls costs
- **Audit Trail**: Complete analysis logging for security review

## 📊 Cost Analysis

- **Model**: GPT-4o-mini (cost-optimized)
- **Average Cost**: $0.001-0.005 per email
- **Monthly Estimate**: ~$45 for 1,000 emails/day
- **Cost Controls**: Token limits, usage monitoring, spending alerts

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

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Rblea97/Phishing_Email_analyzer/issues)
- **Documentation**: [Full Documentation](docs/)
- **Security**: [Security Policy](docs/SECURITY.md)

---

*Built with ❤️ using Flask, OpenAI GPT-4o-mini, and security-first development practices*