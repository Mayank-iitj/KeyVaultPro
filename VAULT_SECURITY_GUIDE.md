# 🔐 Ultra-Secure API Vault - Security Guide

## NoTrust Architecture - Zero-Knowledge Encryption

The API Vault implements a **zero-knowledge security model** where the server NEVER sees your unencrypted API keys. All encryption and decryption happens exclusively in your browser using the Web Crypto API.

---

## 🛡️ Security Features

### 1. **Client-Side Encryption (AES-256-GCM)**
- **Algorithm**: AES-256 in GCM (Galois/Counter Mode)
- **Key Size**: 256 bits
- **Authentication**: Built-in authenticated encryption prevents tampering
- **Implementation**: Browser's Web Crypto API (hardware-accelerated when available)

### 2. **Key Derivation (PBKDF2)**
- **Iterations**: 600,000 (OWASP 2023 recommendation)
- **Hash**: SHA-256
- **Salt**: Cryptographically random 16-byte salt per entry
- **Purpose**: Derives encryption key from your master password

### 3. **Master Password Requirements**
- Minimum 16 characters
- Must include:
  - Uppercase letters (A-Z)
  - Lowercase letters (a-z)
  - Numbers (0-9)
  - Special characters (!@#$%^&*)

### 4. **Auto-Lock Security**
- Automatically locks vault after **5 minutes** of inactivity
- Clears all decrypted data from memory on lock
- Requires master password to unlock again

### 5. **Secure Clipboard**
- Copied API keys auto-clear from clipboard after **30 seconds**
- Prevents accidental exposure through clipboard history

### 6. **Comprehensive Audit Trail**
- Every vault operation logged with:
  - Timestamp
  - Action type (store, retrieve, list, delete)
  - IP address
  - User agent
  - Platform name
- Query your audit logs via `/api/vault/audit?userId={your-user-id}`

---

## 🔒 How It Works

### Storing an API Key

```
1. User enters API key + master password in browser
2. Browser generates random 16-byte salt and 12-byte IV
3. PBKDF2 derives 256-bit encryption key from password + salt
4. AES-256-GCM encrypts the API key
5. Server receives ONLY:
   - Encrypted ciphertext (base64)
   - IV (base64)
   - Salt (base64)
   - Platform name, metadata
6. Server stores encrypted data + metadata
```

**Server NEVER sees**: Your master password or unencrypted API key

### Retrieving an API Key

```
1. Server sends encrypted data + IV + salt to browser
2. User enters master password
3. Browser derives same encryption key using PBKDF2
4. Browser decrypts with AES-256-GCM
5. Decrypted key displayed ONLY in browser
6. Auto-lock timer starts/resets
```

---

## 🚀 Usage Guide

### Access the Vault

1. **Login** to your account at `/login`
2. Navigate to **Dashboard** at `/dashboard`
3. Click **"🔐 Secure Vault"** button
4. Enter your **master password** (creates one on first use)

### Add API Keys

1. Click **"+ Add API Key"**
2. Fill in:
   - **Platform Name**: e.g., Stripe, OpenAI, Twilio
   - **Account/Email**: (optional) identifier
   - **API Key**: Your actual API key
   - **API Secret**: (optional) for keys with secrets
   - **Key Type**: API Key, OAuth Token, JWT, Webhook Secret
   - **Environment**: Production, Staging, Development
3. Click **"Add to Vault"**
4. Your key is encrypted in-browser and stored

### View API Keys

1. Click **"🔓 Reveal API Key"** on any vault item
2. Master password decrypts the key in your browser
3. Click **"Copy"** to copy to clipboard (auto-clears in 30s)

### Delete API Keys

1. Click **"Delete"** on any vault item
2. Confirm deletion
3. Key is soft-deleted (marked inactive, audit trail preserved)

---

## 🔐 Security Best Practices

### ✅ DO:
- Use a unique, strong master password (16+ chars)
- Store master password in a password manager
- Lock vault when stepping away
- Review audit logs regularly for suspicious activity
- Use different master password than your account password

### ❌ DON'T:
- Share your master password with anyone
- Use the same master password across multiple vaults
- Store master password in plain text
- Leave vault unlocked on shared computers

---

## 🛠️ Technical Architecture

### Database Schema

#### `api_vault` Table
```sql
- id: UUID (primary key)
- user_id: UUID (foreign key to users)
- platform_name: TEXT
- account_identifier: TEXT (optional)
- encrypted_api_key: TEXT (base64 AES-GCM ciphertext)
- encrypted_api_secret: TEXT (optional)
- encrypted_additional_data: TEXT (optional)
- encryption_iv: TEXT (base64)
- encryption_salt: TEXT (base64)
- key_type: TEXT
- environment: TEXT
- tags: TEXT[]
- last_accessed_at: TIMESTAMP
- is_active: BOOLEAN
```

#### `vault_audit_log` Table
```sql
- id: UUID
- vault_id: UUID
- user_id: UUID
- action: TEXT (store, retrieve, list, delete)
- ip_address: TEXT
- user_agent: TEXT
- metadata: JSONB
- created_at: TIMESTAMP
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/vault/store` | Store encrypted API key |
| GET | `/api/vault/list` | List all vault items |
| POST | `/api/vault/retrieve` | Get encrypted vault item |
| DELETE | `/api/vault/delete` | Soft-delete vault item |
| GET | `/api/vault/audit` | Get audit logs |

### Encryption Library

**File**: `src/lib/encryption.ts`

**Functions**:
- `encryptData(data, masterPassword)`: Encrypts data with AES-256-GCM
- `decryptData({ encrypted, iv, salt, masterPassword })`: Decrypts data
- `validateMasterPassword(password)`: Validates password strength
- `generateSecurePassword(length)`: Generates random secure password
- `hashMasterPassword(password)`: SHA-256 hash for server verification

---

## 🔍 Security Audit

### Encryption Standards
- ✅ **AES-256-GCM**: NIST approved, industry standard
- ✅ **PBKDF2**: OWASP recommended for key derivation
- ✅ **600,000 iterations**: Protects against brute force
- ✅ **Cryptographically secure random**: IVs and salts

### Code Security
- ✅ **No plaintext storage**: Only encrypted data in database
- ✅ **No password transmission**: Master password never sent to server
- ✅ **Authenticated encryption**: GCM mode prevents tampering
- ✅ **Memory clearing**: Sensitive data cleared on lock
- ✅ **Audit logging**: Complete action trail

### Browser Security
- ✅ **Web Crypto API**: Hardware-backed when available
- ✅ **Same-origin policy**: Isolated from other sites
- ✅ **HTTPS only**: Encrypted in transit (production)

---

## 📊 Threat Model

### What We Protect Against:

✅ **Server Compromise**: Encrypted data unreadable without master password  
✅ **Database Breach**: All API keys stored encrypted  
✅ **Man-in-the-Middle**: HTTPS encrypts all traffic  
✅ **Unauthorized Access**: Authentication + master password required  
✅ **Brute Force**: 600k PBKDF2 iterations make it infeasible  

### What We DON'T Protect Against:

⚠️ **Client-Side Malware**: Keyloggers can capture master password  
⚠️ **Phishing**: Users entering password on fake sites  
⚠️ **Weak Master Passwords**: "password123" defeats encryption  
⚠️ **Browser Compromise**: Malicious extensions can access memory  

---

## 🚨 Security Incidents

If you suspect your vault has been compromised:

1. **Immediately** lock your vault
2. Change your master password
3. Rotate all API keys stored in the vault
4. Review audit logs for suspicious activity
5. Contact platform support if needed

---

## 📝 Compliance & Standards

This vault implementation follows:
- ✅ OWASP Cryptographic Storage Guidelines
- ✅ NIST SP 800-132 (PBKDF2 Recommendations)
- ✅ NIST SP 800-38D (AES-GCM Guidelines)
- ✅ Zero-Knowledge Architecture Principles

---

## 🛡️ Additional Security Recommendations

### For Production Use:
1. Enable **2FA** on your account
2. Use **hardware security keys** when possible
3. Implement **IP whitelisting** for your account
4. Set up **breach detection alerts**
5. Regular **security audits** of vault access logs
6. Use **separate vaults** for different environments

---

## 📞 Security Contact

Found a security vulnerability? Please report responsibly:
- Email: security@your-domain.com
- Do NOT post security issues publicly
- We'll respond within 24 hours

---

**Last Updated**: December 2025  
**Version**: 1.0.0  
**License**: MIT
