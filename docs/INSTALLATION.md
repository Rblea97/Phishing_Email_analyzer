# Installation Guide

Complete installation guide for the AI-Powered Phishing Detection System.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.9 or higher
- **Memory**: Minimum 512MB RAM (2GB recommended)
- **Storage**: 100MB for application + space for database
- **Network**: Internet connection for AI features

### Required Accounts
- **OpenAI Account**: For GPT-4o-mini API access ([Sign up here](https://platform.openai.com/))
- **Git**: For cloning the repository ([Download here](https://git-scm.com/))

## 🚀 Quick Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/Phishing_Email_analyzer.git
cd Phishing_Email_analyzer
```

### 2. Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# Required: Add your OpenAI API key
OPENAI_API_KEY=sk-your-api-key-here
```

### 5. Database Setup
```bash
# Initialize database
python init_db.py

# Run migrations
python migrate_to_phase2.py
python migrate_to_phase3.py
```

### 6. Verify Installation
```bash
# Run tests
python run_tests.py

# Start application
python app_phase2.py
```

Visit `http://localhost:5000` to access the application.

## 🔧 Detailed Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```bash
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=development
PORT=5000
HOST=0.0.0.0

# Database Configuration
DATABASE_PATH=phishing_detector.db

# OpenAI Configuration (Required for AI features)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Security Configuration (Optional)
RATE_LIMIT_PER_MINUTE=10
MAX_DAILY_API_COST=5.00

# Development Configuration (Optional)
DEBUG=true
TESTING=false
```

### OpenAI API Key Setup

1. **Create OpenAI Account**
   - Visit [OpenAI Platform](https://platform.openai.com/)
   - Sign up for an account
   - Add billing information (GPT-4o-mini requires paid account)

2. **Generate API Key**
   - Go to [API Keys page](https://platform.openai.com/api-keys)
   - Click "Create new secret key"
   - Name it (e.g., "Phishing Detector")
   - Copy the key (starts with `sk-`)

3. **Add to Environment**
   ```bash
   echo "OPENAI_API_KEY=sk-your-actual-key-here" >> .env
   ```

4. **Test API Key**
   ```bash
   python test_api_key.py
   ```

## 🗄️ Database Setup Details

### SQLite (Default)
The application uses SQLite by default, which requires no additional setup.

```bash
# Initialize with default settings
python init_db.py

# The database file will be created at:
phishing_detector.db
```

### PostgreSQL (Production)
For production deployment, you can use PostgreSQL:

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Set database URL in .env
DATABASE_URL=postgresql://user:password@localhost/phishing_detector
```

### Database Migrations
```bash
# Phase 2: Rule-based detection
python migrate_to_phase2.py

# Phase 3: AI integration
python migrate_to_phase3.py

# Verify database structure
python -c "from init_db import verify_database; verify_database()"
```

## 🧪 Testing Installation

### Run Test Suite
```bash
# Full test suite
python run_tests.py

# Individual test modules
python -m pytest tests/test_parser.py -v
python -m pytest tests/test_rules.py -v
python -m pytest tests/test_ai.py -v
```

### Manual Testing
```bash
# Start the application
python app_phase2.py

# In another terminal, test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/stats
```

### Upload Test Email
1. Start the application: `python app_phase2.py`
2. Open browser to `http://localhost:5000`
3. Upload a test email from `tests/fixtures/safe_newsletter.eml`
4. Verify both rule-based and AI analysis work

## 🚀 Production Deployment

### Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init

# Set environment variables
railway variables set OPENAI_API_KEY=sk-your-key
railway variables set SECRET_KEY=your-secret-key
railway variables set FLASK_ENV=production

# Deploy
railway up
```

### Docker Deployment
```dockerfile
# Dockerfile example
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app_phase2:app"]
```

### Health Monitoring
```bash
# Check application health
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "ai": {"status": "ok"},
  "database": {"emails": 0}
}
```

## 🔍 Troubleshooting

### Common Issues

#### 1. OpenAI API Key Issues
```bash
# Error: "OpenAI API key not configured"
# Solution: Check .env file and verify key format
grep OPENAI_API_KEY .env
python test_api_key.py
```

#### 2. Database Migration Issues
```bash
# Error: "Table already exists"
# Solution: Drop and recreate database
rm phishing_detector.db
python init_db.py
python migrate_to_phase2.py
python migrate_to_phase3.py
```

#### 3. Import Errors
```bash
# Error: "Module not found"
# Solution: Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

#### 4. Port Already in Use
```bash
# Error: "Port 5000 is already in use"
# Solution: Use different port
PORT=8000 python app_phase2.py
# Or kill process using port 5000
lsof -ti:5000 | xargs kill -9
```

### Performance Issues

#### Slow AI Analysis
- Check internet connection
- Verify OpenAI API status
- Monitor token usage and costs
- Consider rate limiting settings

#### Database Performance
- Check database file permissions
- Monitor disk space
- Consider PostgreSQL for production
- Implement database indexing

## 📞 Support

### Getting Help
- **Documentation**: Check the `docs/` folder
- **Issues**: [GitHub Issues](https://github.com/yourusername/Phishing_Email_analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/Phishing_Email_analyzer/discussions)

### Before Asking for Help
1. Check this installation guide
2. Run the test suite
3. Check the application logs
4. Search existing issues
5. Prepare a minimal reproduction case

---

*For additional help, please see our [Contributing Guide](../CONTRIBUTING.md) or create an issue on GitHub.*