"""
Rate Limiting Middleware (Token Bucket Implementation)
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import RateLimitBucket, APIKey
from app.database.connection import async_session_maker
from app.utils.config import settings


class TokenBucket:
    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        refill_period: float = 1.0
    ):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        refill_amount = (elapsed / self.refill_period) * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + refill_amount)
        self.last_refill = now
    
    def get_retry_after(self) -> float:
        if self.tokens >= 1:
            return 0
        needed = 1 - self.tokens
        return (needed / self.refill_rate) * self.refill_period


class InMemoryRateLimiter:
    def __init__(self):
        self.buckets: Dict[str, Dict[str, TokenBucket]] = {}
    
    def get_bucket(
        self,
        key: str,
        bucket_type: str,
        capacity: int,
        refill_rate: float
    ) -> TokenBucket:
        if key not in self.buckets:
            self.buckets[key] = {}
        
        if bucket_type not in self.buckets[key]:
            self.buckets[key][bucket_type] = TokenBucket(
                capacity=capacity,
                refill_rate=refill_rate
            )
        
        return self.buckets[key][bucket_type]
    
    def cleanup_expired(self, max_age_seconds: int = 3600):
        now = time.time()
        keys_to_remove = []
        
        for key, buckets in self.buckets.items():
            all_expired = True
            for bucket in buckets.values():
                if now - bucket.last_refill < max_age_seconds:
                    all_expired = False
                    break
            if all_expired:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.buckets[key]


rate_limiter = InMemoryRateLimiter()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = ["/docs", "/openapi.json", "/health"]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        api_key_id = getattr(request.state, "api_key_id", None)
        
        if api_key_id:
            api_key: APIKey = getattr(request.state, "api_key", None)
            
            limits = {
                "minute": (
                    api_key.rate_limit_per_minute or settings.rate_limit_per_minute,
                    api_key.rate_limit_per_minute or settings.rate_limit_per_minute
                ),
                "hour": (
                    api_key.rate_limit_per_hour or settings.rate_limit_per_hour,
                    (api_key.rate_limit_per_hour or settings.rate_limit_per_hour) / 60
                ),
                "day": (
                    api_key.rate_limit_per_day or settings.rate_limit_per_day,
                    (api_key.rate_limit_per_day or settings.rate_limit_per_day) / 1440
                )
            }
            
            identifier = f"api_key:{api_key_id}"
        else:
            client_ip = request.client.host if request.client else "unknown"
            identifier = f"ip:{client_ip}"
            
            limits = {
                "minute": (settings.rate_limit_per_minute, settings.rate_limit_per_minute),
                "hour": (settings.rate_limit_per_hour, settings.rate_limit_per_hour / 60),
                "day": (settings.rate_limit_per_day, settings.rate_limit_per_day / 1440)
            }
        
        for period, (capacity, refill_rate) in limits.items():
            bucket = rate_limiter.get_bucket(
                key=identifier,
                bucket_type=period,
                capacity=capacity,
                refill_rate=refill_rate
            )
            
            if not bucket.consume():
                retry_after = bucket.get_retry_after()
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded for {period}",
                        "retry_after_seconds": round(retry_after, 2)
                    },
                    headers={
                        "Retry-After": str(int(retry_after)),
                        "X-RateLimit-Limit": str(capacity),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + retry_after))
                    }
                )
        
        response = await call_next(request)
        
        minute_bucket = rate_limiter.get_bucket(
            key=identifier,
            bucket_type="minute",
            capacity=limits["minute"][0],
            refill_rate=limits["minute"][1]
        )
        
        response.headers["X-RateLimit-Limit"] = str(limits["minute"][0])
        response.headers["X-RateLimit-Remaining"] = str(int(minute_bucket.tokens))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
        return response


class SlidingWindowRateLimiter:
    def __init__(self):
        self.windows: Dict[str, Dict[str, list]] = {}
    
    def is_allowed(
        self,
        key: str,
        window_type: str,
        limit: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        now = time.time()
        
        if key not in self.windows:
            self.windows[key] = {}
        
        if window_type not in self.windows[key]:
            self.windows[key][window_type] = []
        
        window = self.windows[key][window_type]
        
        cutoff = now - window_seconds
        self.windows[key][window_type] = [t for t in window if t > cutoff]
        
        current_count = len(self.windows[key][window_type])
        
        if current_count < limit:
            self.windows[key][window_type].append(now)
            return True, limit - current_count - 1
        
        return False, 0


sliding_window_limiter = SlidingWindowRateLimiter()
