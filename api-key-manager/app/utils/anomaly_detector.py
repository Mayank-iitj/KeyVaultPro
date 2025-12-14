"""
AI-Assisted Security Insights & Anomaly Detection
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.models import AuditLog, APIKey, AnomalyDetection, UsageStats
from app.utils.config import settings
from app.logs.audit import audit_logger


@dataclass
class AnomalyReport:
    anomaly_type: str
    severity: str
    description: str
    detected_value: float
    expected_range: Tuple[float, float]
    api_key_id: str
    recommendation: str


class AnomalyDetector:
    def __init__(self, threshold: float = None):
        self.threshold = threshold or settings.anomaly_threshold
    
    async def analyze_usage_patterns(
        self,
        db: AsyncSession,
        api_key_id: str,
        lookback_hours: int = 24
    ) -> List[AnomalyReport]:
        anomalies = []
        
        cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)
        
        result = await db.execute(
            select(AuditLog).where(
                AuditLog.api_key_id == api_key_id,
                AuditLog.timestamp >= cutoff
            ).order_by(AuditLog.timestamp)
        )
        logs = result.scalars().all()
        
        if len(logs) < 10:
            return anomalies
        
        request_spike = self._detect_request_spike(logs)
        if request_spike:
            anomalies.append(request_spike)
        
        error_spike = self._detect_error_spike(logs)
        if error_spike:
            anomalies.append(error_spike)
        
        ip_anomaly = self._detect_ip_anomaly(logs, api_key_id)
        if ip_anomaly:
            anomalies.append(ip_anomaly)
        
        time_anomaly = self._detect_time_anomaly(logs, api_key_id)
        if time_anomaly:
            anomalies.append(time_anomaly)
        
        return anomalies
    
    def _detect_request_spike(self, logs: List[AuditLog]) -> Optional[AnomalyReport]:
        hourly_counts = {}
        for log in logs:
            hour_key = log.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
        
        if len(hourly_counts) < 3:
            return None
        
        counts = list(hourly_counts.values())
        mean = np.mean(counts)
        std = np.std(counts)
        
        if std == 0:
            return None
        
        latest_count = counts[-1]
        z_score = (latest_count - mean) / std
        
        if z_score > self.threshold:
            return AnomalyReport(
                anomaly_type="request_spike",
                severity="high" if z_score > self.threshold * 2 else "medium",
                description=f"Unusual spike in requests: {latest_count} requests in the last hour",
                detected_value=latest_count,
                expected_range=(max(0, mean - 2*std), mean + 2*std),
                api_key_id=logs[0].api_key_id,
                recommendation="Consider implementing stricter rate limits or investigating the source"
            )
        
        return None
    
    def _detect_error_spike(self, logs: List[AuditLog]) -> Optional[AnomalyReport]:
        error_logs = [l for l in logs if l.status_code and l.status_code >= 400]
        error_rate = len(error_logs) / len(logs) if logs else 0
        
        if error_rate > 0.3:
            return AnomalyReport(
                anomaly_type="error_spike",
                severity="high" if error_rate > 0.5 else "medium",
                description=f"High error rate detected: {error_rate*100:.1f}% of requests failing",
                detected_value=error_rate,
                expected_range=(0, 0.1),
                api_key_id=logs[0].api_key_id if logs else "",
                recommendation="Review API key permissions and client implementation"
            )
        
        return None
    
    def _detect_ip_anomaly(self, logs: List[AuditLog], api_key_id: str) -> Optional[AnomalyReport]:
        unique_ips = set(l.ip_address for l in logs if l.ip_address)
        
        if len(unique_ips) > 10:
            return AnomalyReport(
                anomaly_type="multiple_ips",
                severity="medium",
                description=f"API key used from {len(unique_ips)} different IP addresses",
                detected_value=len(unique_ips),
                expected_range=(1, 5),
                api_key_id=api_key_id,
                recommendation="Consider restricting the API key to specific IP addresses"
            )
        
        return None
    
    def _detect_time_anomaly(self, logs: List[AuditLog], api_key_id: str) -> Optional[AnomalyReport]:
        hours = [l.timestamp.hour for l in logs]
        
        if not hours:
            return None
        
        night_requests = sum(1 for h in hours if h >= 0 and h < 6)
        night_ratio = night_requests / len(hours)
        
        if night_ratio > 0.5 and len(hours) > 20:
            return AnomalyReport(
                anomaly_type="unusual_time_pattern",
                severity="low",
                description=f"{night_ratio*100:.1f}% of requests occur during unusual hours (midnight-6am)",
                detected_value=night_ratio,
                expected_range=(0, 0.2),
                api_key_id=api_key_id,
                recommendation="Verify if this usage pattern is expected for your application"
            )
        
        return None
    
    async def should_recommend_rotation(
        self,
        db: AsyncSession,
        api_key_id: str
    ) -> Tuple[bool, str]:
        result = await db.execute(
            select(APIKey).where(APIKey.id == api_key_id)
        )
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            return False, ""
        
        age_days = (datetime.utcnow() - api_key.created_at).days
        if age_days > 60:
            return True, f"Key is {age_days} days old. Regular rotation recommended."
        
        if api_key.usage_count > 100000:
            return True, f"Key has been used {api_key.usage_count} times. Consider rotation."
        
        anomalies = await self.analyze_usage_patterns(db, api_key_id)
        high_severity = [a for a in anomalies if a.severity == "high"]
        if high_severity:
            return True, f"High severity anomalies detected: {high_severity[0].description}"
        
        return False, ""
    
    async def save_anomaly(
        self,
        db: AsyncSession,
        anomaly: AnomalyReport,
        action_taken: str = None
    ) -> AnomalyDetection:
        detection = AnomalyDetection(
            api_key_id=anomaly.api_key_id,
            anomaly_type=anomaly.anomaly_type,
            severity=anomaly.severity,
            description=anomaly.description,
            detected_value=anomaly.detected_value,
            expected_range=list(anomaly.expected_range),
            action_taken=action_taken
        )
        db.add(detection)
        return detection
    
    async def get_security_insights(
        self,
        db: AsyncSession,
        user_id: str
    ) -> Dict:
        result = await db.execute(
            select(APIKey).where(APIKey.owner_id == user_id)
        )
        keys = result.scalars().all()
        
        insights = {
            "total_keys": len(keys),
            "active_keys": sum(1 for k in keys if k.status.value == "active"),
            "keys_needing_rotation": [],
            "anomalies_detected": [],
            "recommendations": []
        }
        
        for key in keys:
            should_rotate, reason = await self.should_recommend_rotation(db, key.id)
            if should_rotate:
                insights["keys_needing_rotation"].append({
                    "key_id": key.id,
                    "key_name": key.name,
                    "reason": reason
                })
            
            anomalies = await self.analyze_usage_patterns(db, key.id)
            for anomaly in anomalies:
                insights["anomalies_detected"].append({
                    "key_id": key.id,
                    "key_name": key.name,
                    "type": anomaly.anomaly_type,
                    "severity": anomaly.severity,
                    "description": anomaly.description
                })
        
        if insights["keys_needing_rotation"]:
            insights["recommendations"].append(
                "Some API keys should be rotated for security"
            )
        
        keys_without_ip_restriction = [k for k in keys if not k.allowed_ips]
        if keys_without_ip_restriction:
            insights["recommendations"].append(
                f"{len(keys_without_ip_restriction)} keys have no IP restrictions. "
                "Consider adding IP whitelists for sensitive keys."
            )
        
        keys_with_admin = [k for k in keys if "admin" in (k.permissions or [])]
        if keys_with_admin:
            insights["recommendations"].append(
                f"{len(keys_with_admin)} keys have admin permissions. "
                "Review if this level of access is necessary."
            )
        
        return insights


anomaly_detector = AnomalyDetector()
