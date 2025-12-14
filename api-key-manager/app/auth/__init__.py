"""
Authentication Module
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

from app.auth.jwt_handler import JWTHandler
from app.auth.dependencies import get_current_user, require_role, require_permissions

__all__ = ["JWTHandler", "get_current_user", "require_role", "require_permissions"]
