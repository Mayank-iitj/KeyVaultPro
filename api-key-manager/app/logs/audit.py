"""
Audit Logging Service
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AuditLog
from app.utils.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("api_key_manager")


class AuditLogger:
    def __init__(self):
        self.logger = logger
    
    async def log(
        self,
        db: AsyncSession,
        action: str,
        user_id: Optional[str] = None,
        api_key_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        status_code: Optional[int] = None,
        response_time_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        audit_entry = AuditLog(
            action=action,
            user_id=user_id,
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            status_code=status_code,
            response_time_ms=response_time_ms,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        db.add(audit_entry)
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "api_key_id": api_key_id,
            "endpoint": endpoint,
            "method": method,
            "ip_address": ip_address,
            "status_code": status_code,
            "response_time_ms": response_time_ms
        }
        
        if settings.log_format == "json":
            self.logger.info(json.dumps(log_data))
        else:
            self.logger.info(
                f"Action: {action} | User: {user_id} | IP: {ip_address} | "
                f"Endpoint: {endpoint} | Status: {status_code}"
            )
        
        return audit_entry
    
    def info(self, message: str, **kwargs):
        if settings.log_format == "json":
            self.logger.info(json.dumps({"message": message, **kwargs}))
        else:
            self.logger.info(message)
    
    def warning(self, message: str, **kwargs):
        if settings.log_format == "json":
            self.logger.warning(json.dumps({"message": message, **kwargs}))
        else:
            self.logger.warning(message)
    
    def error(self, message: str, **kwargs):
        if settings.log_format == "json":
            self.logger.error(json.dumps({"message": message, **kwargs}))
        else:
            self.logger.error(message)
    
    def critical(self, message: str, **kwargs):
        if settings.log_format == "json":
            self.logger.critical(json.dumps({"message": message, **kwargs}))
        else:
            self.logger.critical(message)


audit_logger = AuditLogger()
