"""
API Key Validation Middleware
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import time
import ipaddress
from datetime import datetime
from typing import Optional, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import APIKey, KeyStatus
from app.database.connection import async_session_maker
from app.security.hashing import hashing_service
from app.security.key_generator import key_generator
from app.logs.audit import audit_logger


class APIKeyValidatorMiddleware(BaseHTTPMiddleware):
    PROTECTED_PATHS = ["/api/v1/protected"]
    EXCLUDED_PATHS = ["/api/v1/auth", "/api/v1/keys", "/docs", "/openapi.json", "/health", "/dashboard"]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        if not any(path.startswith(protected) for protected in self.PROTECTED_PATHS):
            return await call_next(request)
        
        api_key = self._extract_api_key(request)
        
        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "API key required"}
            )
        
        if not key_generator.is_valid_key_format(api_key):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API key format"}
            )
        
        async with async_session_maker() as db:
            key_record, error = await self._validate_key(db, api_key, request)
            
            if error:
                await audit_logger.log(
                    db=db,
                    action="api_key_validation_failed",
                    endpoint=path,
                    method=request.method,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    error_message=error
                )
                await db.commit()
                
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": error}
                )
            
            required_permission = self._get_required_permission(request.method)
            if required_permission not in key_record.permissions:
                await audit_logger.log(
                    db=db,
                    action="api_key_permission_denied",
                    api_key_id=key_record.id,
                    endpoint=path,
                    method=request.method,
                    ip_address=request.client.host if request.client else None,
                    error_message=f"Missing permission: {required_permission}"
                )
                await db.commit()
                
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": f"Missing permission: {required_permission}"}
                )
            
            request.state.api_key = key_record
            request.state.api_key_id = key_record.id
            request.state.permissions = key_record.permissions
            
            start_time = time.time()
            response = await call_next(request)
            response_time = (time.time() - start_time) * 1000
            
            key_record.last_used_at = datetime.utcnow()
            key_record.usage_count += 1
            
            await audit_logger.log(
                db=db,
                action="api_key_used",
                api_key_id=key_record.id,
                endpoint=path,
                method=request.method,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                status_code=response.status_code,
                response_time_ms=response_time
            )
            
            await db.commit()
        
        return response
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key
        
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("ApiKey "):
            return auth_header[7:]
        
        api_key = request.query_params.get("api_key")
        if api_key:
            return api_key
        
        return None
    
    async def _validate_key(
        self,
        db: AsyncSession,
        api_key: str,
        request: Request
    ) -> Tuple[Optional[APIKey], Optional[str]]:
        key_hash = hashing_service.hash_api_key(api_key)
        
        result = await db.execute(
            select(APIKey).where(APIKey.key_hash == key_hash)
        )
        key_record = result.scalar_one_or_none()
        
        if not key_record:
            return None, "Invalid API key"
        
        if key_record.status == KeyStatus.REVOKED:
            return None, "API key has been revoked"
        
        if key_record.status == KeyStatus.DISABLED:
            return None, "API key is disabled"
        
        if key_record.status == KeyStatus.EXPIRED:
            return None, "API key has expired"
        
        if key_record.status == KeyStatus.ROTATING:
            if key_record.grace_period_ends_at and key_record.grace_period_ends_at < datetime.utcnow():
                key_record.status = KeyStatus.REVOKED
                return None, "API key grace period has ended"
        
        if key_record.expires_at and key_record.expires_at < datetime.utcnow():
            key_record.status = KeyStatus.EXPIRED
            return None, "API key has expired"
        
        if key_record.allowed_ips:
            client_ip = request.client.host if request.client else None
            if client_ip and not self._is_ip_allowed(client_ip, key_record.allowed_ips):
                return None, f"IP address {client_ip} not allowed"
        
        if key_record.allowed_user_agents:
            user_agent = request.headers.get("user-agent", "")
            if not any(ua in user_agent for ua in key_record.allowed_user_agents):
                return None, "User agent not allowed"
        
        return key_record, None
    
    def _is_ip_allowed(self, client_ip: str, allowed_ips: list) -> bool:
        try:
            client_addr = ipaddress.ip_address(client_ip)
            for allowed in allowed_ips:
                if "/" in allowed:
                    if client_addr in ipaddress.ip_network(allowed, strict=False):
                        return True
                else:
                    if client_addr == ipaddress.ip_address(allowed):
                        return True
            return False
        except ValueError:
            return False
    
    def _get_required_permission(self, method: str) -> str:
        permission_map = {
            "GET": "read",
            "HEAD": "read",
            "OPTIONS": "read",
            "POST": "write",
            "PUT": "write",
            "PATCH": "write",
            "DELETE": "delete"
        }
        return permission_map.get(method, "read")
