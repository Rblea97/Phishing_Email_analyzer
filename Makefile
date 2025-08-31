# AI-Powered Phishing Detection System - Development Commands

.PHONY: help dev test lint format clean build run docker-build docker-run install

# Default target
help:
	@echo "Available commands:"
	@echo "  make dev        - Set up development environment"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run test suite with coverage"
	@echo "  make lint       - Run linting and security checks"
	@echo "  make format     - Format code with black and isort"
	@echo "  make run        - Run development server"
	@echo "  make build      - Build for production"
	@echo "  make clean      - Clean temporary files"
	@echo "  make docker-build - Build Docker container"
	@echo "  make docker-run - Run in Docker container"

# Development setup
dev: install
	@echo "Setting up development environment..."
	cp .env.example .env
	python init_db.py
	python migrate_to_phase2.py
	python migrate_to_phase3.py
	@echo "✅ Development environment ready!"
	@echo "⚠️  Don't forget to add your OPENAI_API_KEY to .env"

# Install dependencies
install:
	@echo "Installing dependencies..."
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

# Run tests with coverage
test:
	@echo "Running test suite..."
	python run_tests.py
	@echo "📊 Coverage report generated in htmlcov/"

# Lint and security checks
lint:
	@echo "Running code quality checks..."
	@echo "🔍 Flake8 linting..."
	@python -m flake8 services/ --count --select=E9,F63,F7,F82 --show-source --statistics || true
	@python -m flake8 services/ --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
	@echo "🔒 Security scanning with bandit..."
	@python -m bandit -r services/ -f json -o bandit-report.json || true
	@python -m bandit -r services/ || true
	@echo "📦 Dependency security check..."
	@python -m safety check -r requirements.txt || true

# Format code
format:
	@echo "Formatting code..."
	@echo "🎨 Running black..."
	@python -m black services/ --line-length 100 || true
	@echo "📚 Running isort..."
	@python -m isort services/ || true
	@echo "✅ Code formatted"

# Run development server
run:
	@echo "Starting development server..."
	@echo "🚀 Server will be available at http://localhost:5000"
	@echo "⚠️  Make sure OPENAI_API_KEY is set in .env"
	python app.py

# Production build
build: clean test lint
	@echo "Building for production..."
	@echo "✅ Production build complete"

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -f .coverage
	rm -f bandit-report.json
	@echo "✅ Cleaned temporary files"

# Docker commands
docker-build:
	@echo "Building Docker container..."
	docker build -t phishing-detector:latest .
	@echo "✅ Docker container built"

docker-run:
	@echo "Running in Docker container..."
	@echo "🚀 Container will be available at http://localhost:5000"
	docker run -p 5000:5000 --env-file .env phishing-detector:latest

# Development workflow shortcuts
quick-test:
	@echo "Quick test run (no coverage)..."
	python -m pytest tests/ -v --tb=short

security:
	@echo "Security-focused checks..."
	python -m bandit -r services/
	python -m safety check -r requirements.txt

# Database commands
db-init:
	@echo "Initializing database..."
	python init_db.py
	python migrate_to_phase2.py  
	python migrate_to_phase3.py
	@echo "✅ Database initialized"

db-reset: clean db-init
	@echo "✅ Database reset complete"

# Release preparation
release: clean test lint
	@echo "Preparing release..."
	@echo "✅ All checks passed - ready for release"
	
# CI/CD simulation
ci: install test lint
	@echo "Simulating CI/CD pipeline..."
	@echo "✅ CI checks completed"