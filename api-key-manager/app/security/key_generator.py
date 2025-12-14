"""
Cryptographically Secure API Key Generator
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import secrets
import string
import base64
from typing import Tuple


class KeyGenerator:
    PREFIX = "akm"
    SEPARATOR = "_"
    KEY_LENGTH = 32
    
    @classmethod
    def generate_api_key(cls, prefix: str = None) -> Tuple[str, str]:
        prefix = prefix or cls.PREFIX
        random_bytes = secrets.token_bytes(cls.KEY_LENGTH)
        key_body = base64.urlsafe_b64encode(random_bytes).decode().rstrip("=")
        full_key = f"{prefix}{cls.SEPARATOR}{key_body}"
        key_prefix = full_key[:8]
        return full_key, key_prefix
    
    @classmethod
    def generate_refresh_token(cls) -> str:
        return secrets.token_urlsafe(64)
    
    @classmethod
    def generate_secret(cls, length: int = 32) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))
    
    @classmethod
    def generate_request_id(cls) -> str:
        return secrets.token_hex(16)
    
    @classmethod
    def is_valid_key_format(cls, api_key: str) -> bool:
        if not api_key or cls.SEPARATOR not in api_key:
            return False
        parts = api_key.split(cls.SEPARATOR)
        if len(parts) != 2:
            return False
        prefix, body = parts
        if len(prefix) < 2 or len(body) < 20:
            return False
        return True


key_generator = KeyGenerator()
