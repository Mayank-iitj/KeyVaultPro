# API Key Management System

> **Designed & Engineered by Mayank Sharma**  
> 🌐 [https://mayyanks.app](https://mayyanks.app)

A production-ready, secure, and comprehensive API key management system built entirely with Python.

## Features

### Core Features
- 🔐 **Secure Key Generation** - Cryptographically secure API keys using Python's `secrets` module
- 🛡️ **Fine-Grained Permissions** - Scope-based access control (read, write, delete, admin)
- 🔄 **Key Rotation** - Manual and automatic rotation with grace periods
- 📊 **Usage Monitoring** - Comprehensive audit logs with IP tracking
- ⚡ **Rate Limiting** - Token bucket algorithm for abuse prevention
- 🤖 **AI Security Insights** - Anomaly detection using statistical analysis
- 👥 **RBAC** - Role-Based Access Control (Admin, Developer, Read-Only)

### Security Features
- Password hashing with bcrypt (12 rounds)
- API keys stored as SHA-256 hashes only
- Sensitive metadata encrypted with Fernet + PBKDF2
- JWT-based authentication (access + refresh tokens)
- Account lockout after failed login attempts
- IP and User-Agent restrictions per key

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite/PostgreSQL via SQLAlchemy ORM (async)
- **Authentication**: JWT (PyJWT)
- **Encryption**: cryptography (Fernet + PBKDF2)
- **Hashing**: bcrypt
- **Rate Limiting**: Custom Token Bucket implementation
- **UI**: Jinja2 templates (Python-rendered, no JS frameworks)
- **Testing**: pytest + pytest-asyncio

## Quick Start

### Prerequisites
- Python 3.10+
- pip or pipenv

### Installation

```bash
# Clone or navigate to the project
cd api-key-manager

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your settings
```

### Running the Server

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t api-key-manager .
docker run -p 8000:8000 api-key-manager
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout (revoke tokens) |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/auth/change-password` | Change password |

### API Keys
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/keys` | Create new API key |
| GET | `/api/v1/keys` | List all keys |
| GET | `/api/v1/keys/{id}` | Get key details |
| PUT | `/api/v1/keys/{id}` | Update key |
| DELETE | `/api/v1/keys/{id}` | Revoke key |
| POST | `/api/v1/keys/{id}/rotate` | Rotate key |
| POST | `/api/v1/keys/{id}/disable` | Disable key |
| POST | `/api/v1/keys/{id}/enable` | Enable key |

### Audit Logs (Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/logs` | List audit logs |
| GET | `/api/v1/logs/my-keys` | My keys' logs |
| GET | `/api/v1/logs/export/csv` | Export as CSV |
| GET | `/api/v1/logs/export/json` | Export as JSON |
| GET | `/api/v1/logs/stats` | Usage statistics |

## Usage Examples

### Register a User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "myuser",
    "password": "SecurePass123!"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### Create API Key
```bash
curl -X POST "http://localhost:8000/api/v1/keys" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "permissions": ["read", "write"],
    "environment": "production",
    "expires_in_days": 90
  }'
```

### Use API Key
```bash
curl -X GET "http://localhost:8000/api/v1/protected/test" \
  -H "X-API-Key: akm_YOUR_API_KEY_HERE"
```

### Python Example
```python
import httpx

BASE_URL = "http://localhost:8000"

# Login
response = httpx.post(f"{BASE_URL}/api/v1/auth/login", json={
    "email": "user@example.com",
    "password": "SecurePass123!"
})
token = response.json()["access_token"]

# Create API Key
response = httpx.post(
    f"{BASE_URL}/api/v1/keys",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "name": "My API Key",
        "permissions": ["read", "write"]
    }
)
api_key = response.json()["api_key"]

# Use API Key
response = httpx.get(
    f"{BASE_URL}/api/v1/protected/test",
    headers={"X-API-Key": api_key}
)
print(response.json())
```

## Security Design

### Threat Model
1. **Credential Theft** - Mitigated by bcrypt hashing, JWT expiration, refresh token rotation
2. **API Key Leakage** - Keys shown once, stored as hashes, support for rotation
3. **Brute Force** - Account lockout, rate limiting per IP and key
4. **Unauthorized Access** - RBAC, fine-grained permissions, IP restrictions
5. **Data Breach** - Sensitive metadata encrypted, no plaintext keys stored

### Zero-Trust Principles
- Every request validated
- Keys scoped to environment (dev/staging/prod)
- IP and User-Agent restrictions supported
- Anomaly detection for suspicious patterns

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## Project Structure

```
api-key-manager/
├── app/
│   ├── main.py              # FastAPI application
│   ├── auth/                # Authentication module
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   ├── jwt_handler.py
│   │   └── dependencies.py
│   ├── keys/                # API Keys module
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── middleware/          # Custom middleware
│   │   ├── api_key_validator.py
│   │   └── rate_limiter.py
│   ├── security/            # Security utilities
│   │   ├── encryption.py
│   │   ├── hashing.py
│   │   └── key_generator.py
│   ├── database/            # Database models & connection
│   │   ├── connection.py
│   │   └── models.py
│   ├── logs/                # Audit logging
│   │   ├── audit.py
│   │   └── routes.py
│   ├── utils/               # Utilities
│   │   ├── config.py
│   │   ├── anomaly_detector.py
│   │   └── background_tasks.py
│   └── templates/           # Jinja2 templates
├── tests/                   # Test suite
├── migrations/              # Database migrations
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | SQLite |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `MASTER_ENCRYPTION_KEY` | Fernet encryption key | Required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration | 30 |
| `RATE_LIMIT_PER_MINUTE` | Requests per minute | 60 |
| `AUTO_ROTATION_ENABLED` | Enable auto rotation | true |
| `ANOMALY_DETECTION_ENABLED` | Enable anomaly detection | true |

## License

MIT License - See LICENSE file for details.

---

**Designed & Engineered by Mayank Sharma**  
🌐 [https://mayyanks.app](https://mayyanks.app)
