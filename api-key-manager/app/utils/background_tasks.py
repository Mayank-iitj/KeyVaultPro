"""
Background Tasks for Key Rotation and Maintenance
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import asyncio
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import async_session_maker
from app.database.models import APIKey, KeyStatus, User, WebhookEvent
from app.utils.config import settings
from app.logs.audit import audit_logger
from app.utils.anomaly_detector import anomaly_detector


class KeyRotationEngine:
    async def check_expiring_keys(self) -> List[dict]:
        async with async_session_maker() as db:
            warning_date = datetime.utcnow() + timedelta(days=settings.rotation_warning_days)
            
            result = await db.execute(
                select(APIKey).where(
                    APIKey.status == KeyStatus.ACTIVE,
                    APIKey.expires_at != None,
                    APIKey.expires_at <= warning_date,
                    APIKey.expires_at > datetime.utcnow()
                )
            )
            expiring_keys = result.scalars().all()
            
            notifications = []
            for key in expiring_keys:
                days_until_expiry = (key.expires_at - datetime.utcnow()).days
                notifications.append({
                    "key_id": key.id,
                    "key_name": key.name,
                    "owner_id": key.owner_id,
                    "expires_at": key.expires_at.isoformat(),
                    "days_until_expiry": days_until_expiry
                })
                
                await audit_logger.log(
                    db=db,
                    action="key_expiry_warning",
                    api_key_id=key.id,
                    metadata={
                        "days_until_expiry": days_until_expiry,
                        "expires_at": key.expires_at.isoformat()
                    }
                )
            
            await db.commit()
            return notifications
    
    async def expire_old_keys(self) -> int:
        async with async_session_maker() as db:
            result = await db.execute(
                select(APIKey).where(
                    APIKey.status == KeyStatus.ACTIVE,
                    APIKey.expires_at != None,
                    APIKey.expires_at <= datetime.utcnow()
                )
            )
            expired_keys = result.scalars().all()
            
            for key in expired_keys:
                key.status = KeyStatus.EXPIRED
                
                await audit_logger.log(
                    db=db,
                    action="key_auto_expired",
                    api_key_id=key.id,
                    metadata={"expired_at": key.expires_at.isoformat()}
                )
            
            await db.commit()
            return len(expired_keys)
    
    async def complete_rotations(self) -> int:
        async with async_session_maker() as db:
            result = await db.execute(
                select(APIKey).where(
                    APIKey.status == KeyStatus.ROTATING,
                    APIKey.grace_period_ends_at != None,
                    APIKey.grace_period_ends_at <= datetime.utcnow()
                )
            )
            rotating_keys = result.scalars().all()
            
            for key in rotating_keys:
                key.status = KeyStatus.REVOKED
                
                await audit_logger.log(
                    db=db,
                    action="key_rotation_completed",
                    api_key_id=key.id,
                    metadata={"grace_period_ended_at": key.grace_period_ends_at.isoformat()}
                )
            
            await db.commit()
            return len(rotating_keys)
    
    async def run_anomaly_detection(self) -> dict:
        if not settings.anomaly_detection_enabled:
            return {"status": "disabled"}
        
        async with async_session_maker() as db:
            result = await db.execute(
                select(APIKey).where(APIKey.status == KeyStatus.ACTIVE)
            )
            active_keys = result.scalars().all()
            
            total_anomalies = 0
            high_severity_count = 0
            
            for key in active_keys:
                anomalies = await anomaly_detector.analyze_usage_patterns(db, key.id)
                
                for anomaly in anomalies:
                    await anomaly_detector.save_anomaly(db, anomaly)
                    total_anomalies += 1
                    if anomaly.severity == "high":
                        high_severity_count += 1
            
            await db.commit()
            
            return {
                "status": "completed",
                "keys_analyzed": len(active_keys),
                "anomalies_detected": total_anomalies,
                "high_severity": high_severity_count
            }
    
    async def cleanup_rate_limit_buckets(self) -> int:
        from app.middleware.rate_limiter import rate_limiter
        
        initial_count = len(rate_limiter.buckets)
        rate_limiter.cleanup_expired(max_age_seconds=3600)
        cleaned = initial_count - len(rate_limiter.buckets)
        
        return cleaned


rotation_engine = KeyRotationEngine()


async def run_scheduled_tasks():
    while True:
        try:
            expired = await rotation_engine.expire_old_keys()
            audit_logger.info(f"Expired {expired} keys")
            
            completed = await rotation_engine.complete_rotations()
            audit_logger.info(f"Completed {completed} key rotations")
            
            notifications = await rotation_engine.check_expiring_keys()
            if notifications:
                audit_logger.info(f"Sent {len(notifications)} expiry warnings")
            
            anomaly_results = await rotation_engine.run_anomaly_detection()
            if anomaly_results.get("anomalies_detected", 0) > 0:
                audit_logger.warning(
                    f"Detected {anomaly_results['anomalies_detected']} anomalies"
                )
            
            cleaned = await rotation_engine.cleanup_rate_limit_buckets()
            if cleaned > 0:
                audit_logger.info(f"Cleaned {cleaned} rate limit buckets")
            
        except Exception as e:
            audit_logger.error(f"Scheduled task error: {str(e)}")
        
        await asyncio.sleep(300)


class WebhookNotifier:
    async def send_webhook(
        self,
        event_type: str,
        payload: dict
    ) -> bool:
        if not settings.webhook_enabled or not settings.webhook_url:
            return False
        
        async with async_session_maker() as db:
            event = WebhookEvent(
                event_type=event_type,
                payload=payload,
                status="pending"
            )
            db.add(event)
            await db.commit()
            
            try:
                import httpx
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        settings.webhook_url,
                        json={
                            "event": event_type,
                            "data": payload,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        headers={
                            "X-Webhook-Secret": settings.webhook_secret or "",
                            "Content-Type": "application/json"
                        },
                        timeout=10.0
                    )
                    
                    event.status = "delivered" if response.is_success else "failed"
                    event.attempts += 1
                    event.last_attempt_at = datetime.utcnow()
                    
                    if not response.is_success:
                        event.error_message = f"HTTP {response.status_code}"
                    
                    await db.commit()
                    return response.is_success
                    
            except Exception as e:
                event.status = "failed"
                event.attempts += 1
                event.last_attempt_at = datetime.utcnow()
                event.error_message = str(e)
                await db.commit()
                return False


webhook_notifier = WebhookNotifier()
