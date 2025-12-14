"""
Test Configuration
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import pytest
import asyncio
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_api_key_manager.db"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"
os.environ["MASTER_ENCRYPTION_KEY"] = "test-encryption-key-32bytes!!"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
