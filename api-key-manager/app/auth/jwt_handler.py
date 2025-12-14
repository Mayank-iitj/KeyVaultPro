"""
JWT Token Handler
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from pydantic import BaseModel

from app.utils.config import settings


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    iat: datetime
    type: str
    role: Optional[str] = None
    permissions: Optional[list] = None


class JWTHandler:
    @staticmethod
    def create_access_token(
        user_id: str,
        role: str,
        permissions: list = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "role": role,
            "permissions": permissions or []
        }
        
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
    
    @staticmethod
    def create_refresh_token(
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.refresh_token_expire_days
            )
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[TokenPayload]:
        payload = JWTHandler.decode_token(token)
        if not payload:
            return None
        if payload.get("type") != token_type:
            return None
        return TokenPayload(**payload)


jwt_handler = JWTHandler()
