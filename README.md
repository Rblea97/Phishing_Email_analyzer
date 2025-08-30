# 🛡️ AI-Powered Phishing Detection System

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Security](https://img.shields.io/badge/Security-First-red)](docs/SECURITY.md)

> **Advanced cybersecurity tool combining rule-based detection with AI analysis to identify phishing emails with high accuracy and detailed evidence reporting.**

## 🎯 Overview

This project demonstrates sophisticated phishing detection capabilities using a dual-analysis approach:
- **Rule-Based Engine**: 9 weighted detection rules with evidence collection
- **AI Analysis**: GPT-4o-mini integration with structured cybersecurity prompts
- **Professional Interface**: Bootstrap-powered dashboard with tabbed results
- **Production Ready**: Rate limiting, cost monitoring, and comprehensive security

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

### Prerequisites
- Python 3.9+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

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

### Database Setup

```bash
# Initialize database
python init_db.py

# Run migrations for full feature set
python migrate_to_phase2.py
python migrate_to_phase3.py
```

### Run the Application

```bash
python app_phase2.py
# Visit: http://localhost:5000
```

### Run Tests

```bash
python run_tests.py
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
- **Analysis Speed**: <500ms rule-based, <2s with AI
- **Accuracy**: 90%+ on test fixtures with detailed evidence
- **Cost Efficiency**: ~$0.001-0.005 per email analysis
- **Scalability**: Rate-limited for production deployment

## 🛠️ Technology Stack

- **Backend**: Flask 3.0.0, Python 3.9+
- **AI Integration**: OpenAI GPT-4o-mini API
- **Database**: SQLite (development) → PostgreSQL (production)
- **Frontend**: Bootstrap 5, responsive design
- **Security**: Flask-Limiter, comprehensive input validation
- **Testing**: Pytest with 90%+ coverage
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