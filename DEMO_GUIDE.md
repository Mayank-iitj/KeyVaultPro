# 🚀 API Key Manager - Live Workflow Demo

## Overview
An interactive demonstration of the complete API Key Management System workflow, showcasing all features from user registration to API key rotation.

## What This Demo Does

The live demo runs through **6 automated steps** that demonstrate the entire API key lifecycle:

### Step 1: Register User
- Creates a new user account with email and password
- Uses bcrypt for password hashing
- Returns user details with role assignment

### Step 2: Login & Get Token  
- Authenticates the user with credentials
- Generates JWT access and refresh tokens
- Displays truncated token for security

### Step 3: Create API Key
- Uses JWT bearer token for authentication
- Generates cryptographically secure API key (format: `akm_xxx...`)
- Assigns permissions: `read`, `write`
- Returns key metadata and full API key (shown once)

### Step 4: Test Protected Endpoint
- Makes authenticated request using the API key
- Validates key format and permissions
- Demonstrates middleware validation
- Returns success message with request details

### Step 5: View API Keys
- Lists all API keys for the authenticated user
- Shows metadata: name, prefix, permissions, status
- Excludes the actual key values (security)

### Step 6: Rotate API Key
- Initiates key rotation with grace period
- Generates new key while keeping old key valid temporarily
- Returns both old and new key information
- Demonstrates zero-downtime key updates

## Technical Implementation

### Frontend (Next.js + TypeScript)
- **Component**: `/src/components/WorkflowDemo.tsx`
- Real-time status updates with visual feedback
- Collapsible code snippets showing cURL commands
- JSON response viewers
- Session credential display

### API Proxy (Next.js API Route)
- **Endpoint**: `/src/app/api/proxy/route.ts`
- Proxies requests from browser to Python backend
- Handles CORS and request forwarding
- Returns responses with proper status codes

### Backend (Python + FastAPI)
- **Base URL**: `http://localhost:8000`
- **Endpoints**:
  - `POST /api/v1/auth/register` - User registration
  - `POST /api/v1/auth/login` - Authentication
  - `POST /api/v1/keys` - Create API key
  - `GET /api/v1/protected/test` - Test endpoint
  - `GET /api/v1/keys` - List keys
  - `POST /api/v1/keys/{id}/rotate` - Rotate key

## How to Use

### Method 1: Live Demo Button
1. Navigate to the homepage
2. Click "Live Demo" in the navigation
3. Click "▶️ Run Complete Demo"
4. Watch all 6 steps execute automatically
5. Expand details to view cURL commands and responses
6. Click "🔄 Reset" to run again

### Method 2: Manual API Testing
Use the provided cURL commands in "Quick Start" section:

```bash
# 1. Register
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser", "password": "SecurePass123!"}'

# 2. Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'

# 3. Create Key (use token from step 2)
curl -X POST "http://localhost:8000/api/v1/keys" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "permissions": ["read", "write"]}'

# 4. Test API Key (use key from step 3)
curl -X GET "http://localhost:8000/api/v1/protected/test" \
  -H "X-API-Key: akm_YOUR_KEY_HERE"
```

## Visual Indicators

### Status Icons
- ⏸️ **Pending** - Not started yet
- ⏳ **Loading** - Currently executing
- ✅ **Success** - Completed successfully
- ❌ **Error** - Failed with error message

### Border Colors
- **Gray** - Pending/idle
- **Indigo glow** - Active/loading
- **Green** - Success
- **Red** - Error

## Security Features Demonstrated

1. **Password Hashing** - bcrypt with salt
2. **JWT Authentication** - Bearer token validation
3. **API Key Format** - `akm_` prefix + base64url encoded bytes
4. **Key Hashing** - SHA-256 for storage
5. **One-Time Display** - Keys shown only at creation
6. **Permission Scoping** - Granular access control
7. **Key Rotation** - Zero-downtime updates
8. **Rate Limiting** - Token bucket algorithm
9. **Audit Logging** - Every request tracked

## Behind the Scenes

### Authentication Flow
```
User → Next.js Proxy → FastAPI Backend
  ↓
JWT Token Generated
  ↓
Token stored in state
  ↓
Used for subsequent requests
```

### API Key Validation Flow
```
Request with X-API-Key header
  ↓
Middleware extracts key
  ↓
Format validation (akm_xxx)
  ↓
Hash and database lookup
  ↓
Permission check
  ↓
Rate limit check
  ↓
Audit log entry
  ↓
Request allowed/denied
```

## Credits

**Designed & Engineered by Mayank Sharma**  
🌐 [https://mayyanks.app](https://mayyanks.app)

---

## Next Steps

Try the Python Dashboard:
- Navigate to `http://localhost:8000/` in a new tab
- View admin panel with Jinja2 templates
- Access audit logs and statistics
- Manage keys through web interface

Run Tests:
```bash
cd api-key-manager
pytest tests/ -v
```

Deploy with Docker:
```bash
cd api-key-manager
docker-compose up -d
```

## Support

For issues or questions:
1. Check `api-key-manager/TEST_RESULTS.md`
2. Review `api-key-manager/README.md`
3. Contact: [Mayank Sharma](https://mayyanks.app)
