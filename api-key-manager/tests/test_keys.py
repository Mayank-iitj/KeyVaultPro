"""
API Keys Tests
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.connection import engine
from app.database.models import Base


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_token(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }
    )
    
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_api_key(client, auth_token):
    response = await client.post(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "name": "Test Key",
            "permissions": ["read", "write"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Key"
    assert "api_key" in data
    assert data["api_key"].startswith("akm_")
    assert data["permissions"] == ["read", "write"]


@pytest.mark.asyncio
async def test_list_api_keys(client, auth_token):
    await client.post(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "Key 1", "permissions": ["read"]}
    )
    await client.post(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "Key 2", "permissions": ["write"]}
    )
    
    response = await client.get(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_api_key(client, auth_token):
    create_response = await client.post(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "Test Key", "permissions": ["read"]}
    )
    key_id = create_response.json()["id"]
    
    response = await client.get(
        f"/api/v1/keys/{key_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == key_id
    assert data["name"] == "Test Key"


@pytest.mark.asyncio
async def test_update_api_key(client, auth_token):
    create_response = await client.post(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "Test Key", "permissions": ["read"]}
    )
    key_id = create_response.json()["id"]
    
    response = await client.put(
        f"/api/v1/keys/{key_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "Updated Key", "permissions": ["read", "write"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Key"
    assert data["permissions"] == ["read", "write"]


@pytest.mark.asyncio
async def test_disable_api_key(client, auth_token):
    create_response = await client.post(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "Test Key", "permissions": ["read"]}
    )
    key_id = create_response.json()["id"]
    
    response = await client.post(
        f"/api/v1/keys/{key_id}/disable",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "disabled"


@pytest.mark.asyncio
async def test_enable_api_key(client, auth_token):
    create_response = await client.post(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "Test Key", "permissions": ["read"]}
    )
    key_id = create_response.json()["id"]
    
    await client.post(
        f"/api/v1/keys/{key_id}/disable",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    response = await client.post(
        f"/api/v1/keys/{key_id}/enable",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "active"


@pytest.mark.asyncio
async def test_revoke_api_key(client, auth_token):
    create_response = await client.post(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "Test Key", "permissions": ["read"]}
    )
    key_id = create_response.json()["id"]
    
    response = await client.delete(
        f"/api/v1/keys/{key_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204
    
    get_response = await client.get(
        f"/api/v1/keys/{key_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert get_response.json()["status"] == "revoked"


@pytest.mark.asyncio
async def test_rotate_api_key(client, auth_token):
    create_response = await client.post(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "Test Key", "permissions": ["read"]}
    )
    key_id = create_response.json()["id"]
    
    response = await client.post(
        f"/api/v1/keys/{key_id}/rotate",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"grace_period_hours": 24}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["old_key_id"] == key_id
    assert "new_key" in data
    assert data["new_key"]["api_key"].startswith("akm_")


@pytest.mark.asyncio
async def test_key_with_ip_restriction(client, auth_token):
    response = await client.post(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "name": "Restricted Key",
            "permissions": ["read"],
            "allowed_ips": ["192.168.1.0/24", "10.0.0.1"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["allowed_ips"] == ["192.168.1.0/24", "10.0.0.1"]


@pytest.mark.asyncio
async def test_key_with_expiration(client, auth_token):
    response = await client.post(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "name": "Expiring Key",
            "permissions": ["read"],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["expires_at"] is not None
