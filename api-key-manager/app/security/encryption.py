"""
Encryption Service using Fernet + PBKDF2
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from app.utils.config import settings


class EncryptionService:
    def __init__(self, master_key: Optional[str] = None):
        self._master_key = master_key or settings.master_encryption_key
        if not self._master_key:
            self._master_key = self._generate_master_key()
        self._fernet = self._create_fernet()
    
    @staticmethod
    def _generate_master_key() -> str:
        return base64.urlsafe_b64encode(os.urandom(32)).decode()
    
    def _create_fernet(self) -> Fernet:
        salt = b"api_key_manager_salt_v1"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(self._master_key.encode())
        )
        return Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        encrypted = self._fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            decoded = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            raise ValueError("Failed to decrypt data")
    
    def encrypt_dict(self, data: dict) -> str:
        import json
        return self.encrypt(json.dumps(data))
    
    def decrypt_dict(self, ciphertext: str) -> dict:
        import json
        decrypted = self.decrypt(ciphertext)
        return json.loads(decrypted) if decrypted else {}


encryption_service = EncryptionService()
