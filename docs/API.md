# API Documentation

Complete API reference for the AI-Powered Phishing Detection System.

## 🌐 Base URL

- **Development**: `http://localhost:5000`
- **Production**: `https://your-app.railway.app`

## 📋 API Overview

The application provides a RESTful API with the following endpoints:

| Endpoint | Method | Purpose | Rate Limited |
|----------|--------|---------|--------------|
| `/` | GET | Main upload interface | No |
| `/upload` | POST | Analyze uploaded email | Yes (10/min) |
| `/analysis/<id>` | GET | Get analysis results | No |
| `/analyses` | GET | List all analyses | No |
| `/stats` | GET | System statistics | No |
| `/health` | GET | Health check | No |

## 🔐 Authentication

Currently, the API does not require authentication. Rate limiting is implemented based on IP address.

## 📝 Endpoints

### 1. Upload and Analyze Email

**Endpoint**: `POST /upload`  
**Rate Limit**: 10 requests per minute per IP  
**Content-Type**: `multipart/form-data`

#### Request
```bash
curl -X POST \
  -F "email_file=@sample.eml" \
  http://localhost:5000/upload
```

#### Parameters
- `email_file` (file, required): Email file (.eml, .txt, .msg)
  - Maximum size: 25MB
  - Supported formats: EML, MSG, plain text

#### Response
```json
{
  "success": true,
  "analysis_id": 123,
  "redirect_url": "/analysis/123",
  "message": "Email analyzed successfully"
}
```

#### Error Response
```json
{
  "success": false,
  "error": "File too large. Maximum size is 25MB.",
  "error_code": "FILE_TOO_LARGE"
}
```

### 2. Get Analysis Results

**Endpoint**: `GET /analysis/<id>`  
**Rate Limit**: None

#### Request
```bash
curl http://localhost:5000/analysis/123
```

#### Response (JSON)
```json
{
  "email": {
    "id": 123,
    "filename": "sample.eml",
    "size_bytes": 4567,
    "uploaded_at": "2025-08-30T16:30:00Z",
    "sha256": "a1b2c3d4..."
  },
  "rule_analysis": {
    "score": 15,
    "label": "Suspicious",
    "confidence": 0.75,
    "evidence": [
      {
        "rule_id": "HEADER_MISMATCH",
        "description": "Display name domain differs from sender domain",
        "weight": 15,
        "details": "Display: 'PayPal' <noreply@suspicious-domain.com>"
      }
    ],
    "processing_time_ms": 245,
    "rules_checked": 9,
    "rules_fired": 1
  },
  "ai_analysis": {
    "score": 85,
    "label": "Likely Phishing",
    "evidence": [
      {
        "id": "SOCIAL_ENGINEERING",
        "description": "Uses urgent language and threats",
        "weight": 30
      },
      {
        "id": "DOMAIN_SPOOFING",
        "description": "Domain mimics legitimate service",
        "weight": 25
      }
    ],
    "tokens_used": 1247,
    "cost_estimate": 0.003,
    "processing_time_ms": 1850,
    "success": true
  },
  "parsed_content": {
    "headers": {
      "from": "PayPal <noreply@suspicious-domain.com>",
      "to": "user@example.com",
      "subject": "Urgent: Account Suspended",
      "date": "2025-08-30T15:30:00Z"
    },
    "text_body": "Your account has been suspended...",
    "urls": [
      {
        "url": "https://suspicious-domain.com/login",
        "domain": "suspicious-domain.com",
        "context": "Click here to reactivate"
      }
    ]
  }
}
```

### 3. List All Analyses

**Endpoint**: `GET /analyses`  
**Rate Limit**: None

#### Request
```bash
curl http://localhost:5000/analyses
```

#### Query Parameters
- `limit` (int, optional): Number of results (default: 50, max: 100)
- `offset` (int, optional): Pagination offset (default: 0)
- `order` (string, optional): Sort order - `newest` or `oldest` (default: `newest`)

#### Response
```json
{
  "analyses": [
    {
      "id": 123,
      "filename": "sample.eml",
      "uploaded_at": "2025-08-30T16:30:00Z",
      "rule_score": 15,
      "rule_label": "Suspicious",
      "ai_score": 85,
      "ai_label": "Likely Phishing",
      "processing_time_ms": 2095
    }
  ],
  "total": 1,
  "has_more": false
}
```

### 4. System Statistics

**Endpoint**: `GET /stats`  
**Rate Limit**: None

#### Request
```bash
curl http://localhost:5000/stats
```

#### Response
```json
{
  "total_analyses": 156,
  "analyses_today": 23,
  "rule_analysis": {
    "avg_score": 12.5,
    "avg_processing_time_ms": 245,
    "label_distribution": {
      "Likely Safe": 89,
      "Suspicious": 45,
      "Likely Phishing": 22
    }
  },
  "ai_analysis": {
    "enabled": true,
    "total_analyses": 143,
    "success_rate": 0.956,
    "avg_score": 28.7,
    "avg_processing_time_ms": 1847,
    "total_tokens_used": 187420,
    "total_cost": 45.67,
    "daily_cost": 3.21,
    "label_distribution": {
      "Likely Safe": 76,
      "Suspicious": 38,
      "Likely Phishing": 29
    }
  },
  "performance": {
    "uptime_seconds": 3600,
    "avg_response_time_ms": 234
  }
}
```

### 5. Health Check

**Endpoint**: `GET /health`  
**Rate Limit**: None

#### Request
```bash
curl http://localhost:5000/health
```

#### Response (Healthy)
```json
{
  "status": "healthy",
  "timestamp": "2025-08-30T16:45:00Z",
  "version": "3.0.0",
  "database": {
    "status": "ok",
    "emails": 156,
    "analyses": 156,
    "ai_analyses": 143
  },
  "services": {
    "parser": "ok",
    "rules": {
      "status": "ok",
      "rules_loaded": 9
    },
    "ai": {
      "status": "ok",
      "model": "gpt-4o-mini",
      "daily_tokens": 15420,
      "daily_cost": 3.21
    }
  }
}
```

#### Response (Unhealthy)
```json
{
  "status": "unhealthy",
  "timestamp": "2025-08-30T16:45:00Z",
  "errors": [
    "OpenAI API key not configured",
    "Database connection failed"
  ],
  "database": {
    "status": "error",
    "error": "Connection timeout"
  },
  "services": {
    "parser": "ok",
    "rules": "ok",
    "ai": {
      "status": "error",
      "error": "API key not configured"
    }
  }
}
```

## 🚫 Error Responses

### Standard Error Format
```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "details": {
    "field": "Additional context"
  }
}
```

### HTTP Status Codes

| Code | Description | When |
|------|-------------|------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid input, malformed request |
| 413 | Payload Too Large | File exceeds size limit |
| 415 | Unsupported Media Type | Invalid file format |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Application error |
| 503 | Service Unavailable | AI service unavailable |

### Error Codes

#### Upload Errors
- `NO_FILE_SELECTED`: No file provided
- `INVALID_FILE_TYPE`: Unsupported file format
- `FILE_TOO_LARGE`: File exceeds 25MB limit
- `PARSING_FAILED`: Email parsing error
- `ANALYSIS_FAILED`: Analysis engine error

#### Rate Limiting
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `AI_QUOTA_EXCEEDED`: Daily AI limit reached
- `COST_LIMIT_EXCEEDED`: Daily cost limit reached

#### Service Errors
- `AI_UNAVAILABLE`: OpenAI API unavailable
- `DATABASE_ERROR`: Database connection failed
- `INVALID_ANALYSIS_ID`: Analysis not found

## 🔄 Rate Limiting

### Limits
- **File Upload**: 10 requests per minute per IP
- **AI Analysis**: Included in upload limit
- **Other Endpoints**: No limit

### Rate Limit Headers
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1693411200
Retry-After: 42
```

### Rate Limit Error
```json
{
  "success": false,
  "error": "Rate limit exceeded. Try again in 42 seconds.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 42
}
```

## 💰 Cost Tracking

### AI Cost Information
Each AI analysis includes cost tracking:

```json
{
  "ai_analysis": {
    "tokens_used": 1247,
    "cost_estimate": 0.003,
    "model": "gpt-4o-mini"
  }
}
```

### Daily Cost Limits
- Default: $5.00 per day
- Configurable via `MAX_DAILY_API_COST` environment variable
- Requests blocked when limit exceeded

## 🧪 Testing the API

### Using cURL

#### Upload Test Email
```bash
curl -X POST \
  -F "email_file=@tests/fixtures/safe_newsletter.eml" \
  -H "Accept: application/json" \
  http://localhost:5000/upload
```

#### Get Results
```bash
# Get analysis results
curl http://localhost:5000/analysis/1

# Get statistics
curl http://localhost:5000/stats

# Check health
curl http://localhost:5000/health
```

### Using Python requests

```python
import requests

# Upload email
with open('tests/fixtures/safe_newsletter.eml', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/upload',
        files={'email_file': f}
    )
    
result = response.json()
analysis_id = result['analysis_id']

# Get analysis results  
analysis = requests.get(f'http://localhost:5000/analysis/{analysis_id}')
print(analysis.json())
```

### Using JavaScript/Fetch

```javascript
// Upload email
const formData = new FormData();
formData.append('email_file', fileInput.files[0]);

fetch('/upload', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        window.location.href = data.redirect_url;
    } else {
        console.error('Upload failed:', data.error);
    }
});
```

## 🔒 Security Considerations

### Input Validation
- All file uploads are validated for type and size
- Email content is sanitized before AI processing
- Database queries use parameterized statements

### API Security
- Rate limiting prevents abuse
- No authentication required (consider adding for production)
- CORS headers configured for web access
- Security headers implemented

### Data Privacy
- Email content not stored permanently in logs
- AI analysis uses only sanitized metadata
- Personal information filtered before external API calls

## 📞 Support

For API questions or issues:
- Check the [Installation Guide](INSTALLATION.md)
- Review the [Security Policy](SECURITY.md)
- Create an issue on [GitHub](https://github.com/yourusername/Phishing_Email_analyzer/issues)

---

*API documentation version 1.0 - Last updated: 2025-08-30*