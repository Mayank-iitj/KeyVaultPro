"""
Hashing Service using bcrypt
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import hashlib
import bcrypt
from typing import Tuple


class HashingService:
    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), hashed_password.encode())
        except Exception:
            return False
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def create_key_prefix(api_key: str, length: int = 8) -> str:
        return api_key[:length]


hashing_service = HashingService()
