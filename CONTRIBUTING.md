# Contributing to AI-Powered Phishing Detection System

Thank you for your interest in contributing to this cybersecurity project! This guide will help you get started.

## 🚀 Quick Start for Contributors

### Prerequisites
- Python 3.9+
- Git
- OpenAI API key for testing AI features

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/Phishing_Email_analyzer.git
   cd Phishing_Email_analyzer
   ```

2. **Environment Setup**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   python init_db.py
   python migrate_to_phase2.py
   python migrate_to_phase3.py
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Add your OpenAI API key for testing
   ```

5. **Run Tests**
   ```bash
   python run_tests.py
   ```

## 🎯 Ways to Contribute

### 🐛 Bug Reports
- Use the [GitHub Issues](https://github.com/yourusername/Phishing_Email_analyzer/issues) template
- Include steps to reproduce
- Provide system information (OS, Python version)
- Include relevant logs or error messages

### 💡 Feature Requests
- Check existing issues first
- Describe the use case and expected behavior
- Consider security implications
- Provide mockups or examples if applicable

### 🔧 Code Contributions
- Fork the repository
- Create a feature branch (`git checkout -b feature/amazing-feature`)
- Follow the coding standards below
- Add tests for new functionality
- Update documentation as needed

## 📋 Coding Standards

### Python Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use docstrings for all functions and classes

### Security Requirements
- **Never commit API keys or secrets**
- Validate all user inputs
- Follow secure coding practices
- Add security tests for new features

### Testing Requirements
- Maintain 90%+ test coverage
- Write unit tests for all new functions
- Include integration tests for new endpoints
- Mock external API calls (OpenAI, etc.)

### Documentation
- Update README.md for major changes
- Add docstrings to all new functions
- Include inline comments for complex logic
- Update API documentation if applicable

## 🔒 Security Guidelines

### Responsible Disclosure
- Report security vulnerabilities privately
- Email: [security contact if you have one]
- Do not create public issues for security bugs

### AI Integration Standards
- Mock all AI calls in tests
- Implement proper token limiting
- Add cost monitoring for new AI features
- Validate all AI responses with JSON schemas

### Data Handling
- Never log sensitive email content
- Sanitize inputs before AI processing
- Implement proper error handling
- Follow data retention policies

## 📝 Commit Message Format

Use conventional commits format:

```
type(scope): brief description

feat(ai): add structured prompt engineering
fix(parser): resolve Unicode handling issue
docs(readme): update installation instructions
test(rules): add phishing detection test cases
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/modifications
- `refactor`: Code refactoring
- `style`: Code style changes
- `chore`: Maintenance tasks

## 🧪 Testing Guidelines

### Running Tests
```bash
# All tests
python run_tests.py

# Specific test files
python -m pytest tests/test_parser.py -v
python -m pytest tests/test_ai.py -v

# With coverage
python -m pytest --cov=services --cov-report=html
```

### Test Structure
```
tests/
├── fixtures/          # Email samples for testing
├── test_parser.py     # Email parsing tests
├── test_rules.py      # Rule engine tests
├── test_ai.py         # AI integration tests (mocked)
└── test_integration.py # End-to-end tests
```

### Adding Test Cases
- Use realistic email fixtures
- Test both positive and negative cases
- Mock external API calls
- Validate error handling

## 📊 Performance Considerations

### Performance Targets
- Rule-based analysis: <500ms
- AI analysis: <2000ms
- Combined analysis: <2500ms
- Database queries: <100ms

### Optimization Guidelines
- Profile code for bottlenecks
- Use efficient database queries
- Implement appropriate caching
- Monitor memory usage

## 🚀 Deployment Considerations

### Railway Deployment
- Ensure environment variables are documented
- Test with production-like settings
- Verify health check endpoints
- Consider rate limiting implications

### Database Migrations
- Write reversible migrations
- Test with sample data
- Document schema changes
- Consider performance impact

## 📖 Documentation Standards

### Code Documentation
```python
def analyze_email(email_content: str, use_ai: bool = True) -> AnalysisResult:
    """
    Analyze an email for phishing indicators.
    
    Args:
        email_content: Raw email content to analyze
        use_ai: Whether to include AI analysis (default: True)
        
    Returns:
        AnalysisResult containing scores, labels, and evidence
        
    Raises:
        ValidationError: If email content is invalid
        AIError: If AI analysis fails (when use_ai=True)
    """
```

### API Documentation
- Document all endpoints
- Include example requests/responses
- Note rate limiting behavior
- Describe error conditions

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow professional communication standards

### Review Process
- All changes require review
- Address feedback promptly
- Test locally before requesting review
- Keep changes focused and atomic

## 📞 Getting Help

- **General Questions**: Open a GitHub discussion
- **Bug Reports**: Use GitHub issues
- **Security Issues**: Contact privately
- **Documentation**: Check the docs/ folder

## 🏆 Recognition

Contributors will be acknowledged in:
- README.md contributors section
- Release notes for significant contributions
- Project documentation

Thank you for helping make the web safer! 🛡️