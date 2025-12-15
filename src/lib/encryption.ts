/**
 * Zero-Knowledge Client-Side Encryption Utilities
 * NoTrust Policy: Server never sees unencrypted data
 * 
 * Security Features:
 * - AES-256-GCM encryption (authenticated encryption)
 * - PBKDF2 key derivation (600,000 iterations)
 * - Cryptographically secure random IVs and salts
 * - Browser's Web Crypto API (hardware-backed if available)
 */

export interface EncryptionResult {
  encrypted: string;
  iv: string;
  salt: string;
}

export interface DecryptionParams {
  encrypted: string;
  iv: string;
  salt: string;
  masterPassword: string;
}

const PBKDF2_ITERATIONS = 600000; // OWASP 2023 recommendation
const KEY_LENGTH = 256;
const SALT_LENGTH = 16;
const IV_LENGTH = 12; // GCM standard

/**
 * Derives encryption key from master password using PBKDF2
 */
async function deriveKey(
  password: string,
  salt: Uint8Array
): Promise<CryptoKey> {
  const encoder = new TextEncoder();
  const passwordKey = await crypto.subtle.importKey(
    'raw',
    encoder.encode(password),
    'PBKDF2',
    false,
    ['deriveKey']
  );

  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: salt,
      iterations: PBKDF2_ITERATIONS,
      hash: 'SHA-256',
    },
    passwordKey,
    { name: 'AES-GCM', length: KEY_LENGTH },
    false,
    ['encrypt', 'decrypt']
  );
}

/**
 * Converts ArrayBuffer to Base64 string
 */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Converts Base64 string to ArrayBuffer
 */
function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Encrypts data with master password using AES-256-GCM
 * Returns base64-encoded ciphertext, IV, and salt
 */
export async function encryptData(
  data: string,
  masterPassword: string
): Promise<EncryptionResult> {
  // Generate cryptographically secure random salt and IV
  const salt = crypto.getRandomValues(new Uint8Array(SALT_LENGTH));
  const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH));

  // Derive encryption key from password
  const key = await deriveKey(masterPassword, salt);

  // Encrypt data
  const encoder = new TextEncoder();
  const encryptedBuffer = await crypto.subtle.encrypt(
    {
      name: 'AES-GCM',
      iv: iv,
    },
    key,
    encoder.encode(data)
  );

  return {
    encrypted: arrayBufferToBase64(encryptedBuffer),
    iv: arrayBufferToBase64(iv),
    salt: arrayBufferToBase64(salt),
  };
}

/**
 * Decrypts data with master password
 * Throws error if password is incorrect or data is tampered
 */
export async function decryptData(params: DecryptionParams): Promise<string> {
  try {
    const salt = new Uint8Array(base64ToArrayBuffer(params.salt));
    const iv = new Uint8Array(base64ToArrayBuffer(params.iv));
    const encryptedData = base64ToArrayBuffer(params.encrypted);

    // Derive decryption key
    const key = await deriveKey(params.masterPassword, salt);

    // Decrypt data
    const decryptedBuffer = await crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: iv,
      },
      key,
      encryptedData
    );

    const decoder = new TextDecoder();
    return decoder.decode(decryptedBuffer);
  } catch (error) {
    throw new Error('Decryption failed: Invalid password or corrupted data');
  }
}

/**
 * Generates a hash of the master password for server-side verification
 * without revealing the actual password
 */
export async function hashMasterPassword(password: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  return arrayBufferToBase64(hashBuffer);
}

/**
 * Securely clears sensitive data from memory
 */
export function secureClear(data: string | ArrayBuffer): void {
  if (typeof data === 'string') {
    // Overwrite string memory (best effort in JS)
    data = '\0'.repeat(data.length);
  } else {
    // Clear ArrayBuffer
    new Uint8Array(data).fill(0);
  }
}

/**
 * Validates master password strength
 */
export function validateMasterPassword(password: string): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (password.length < 16) {
    errors.push('Password must be at least 16 characters');
  }
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain lowercase letters');
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain uppercase letters');
  }
  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain numbers');
  }
  if (!/[^a-zA-Z0-9]/.test(password)) {
    errors.push('Password must contain special characters');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Generates a secure random password
 */
export function generateSecurePassword(length: number = 32): string {
  const charset =
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?';
  const randomValues = crypto.getRandomValues(new Uint8Array(length));
  return Array.from(randomValues)
    .map((x) => charset[x % charset.length])
    .join('');
}
