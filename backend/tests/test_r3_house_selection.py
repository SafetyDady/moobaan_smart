"""
Phase R.3 Tests: House Selection for Residents

Tests for:
1. GET /api/resident/houses - List houses
2. POST /api/resident/select-house - Select house
3. POST /api/resident/switch-house - Switch house
4. require_active_house dependency
5. Cross-house access prevention
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

import httpx
from httpx import ASGITransport

# Import app for testing
from app.main import app
from app.services.otp_service import OTPConfig, otp_store


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture
async def client():
    """Async test client"""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def reset_otp_store():
    """Reset OTP store before test"""
    otp_store._store.clear()
    otp_store._rate_limits.clear()
    yield
    otp_store._store.clear()
    otp_store._rate_limits.clear()


# ============================================================
# Helper Functions for Tests
# ============================================================

async def login_resident(client: httpx.AsyncClient, phone: str = "0812345678") -> dict:
    """
    Helper to login a resident and get cookies.
    Returns dict with cookies.
    """
    otp_store._store.clear()
    otp_store._rate_limits.clear()
    
    # Request OTP
    await client.post(
        "/api/resident/login/request-otp",
        json={"phone": phone}
    )
    
    # Verify OTP
    response = await client.post(
        "/api/resident/login/verify-otp",
        json={"phone": phone, "otp": OTPConfig.MOCK_CODE}
    )
    
    assert response.status_code == 200
    return dict(response.cookies)


# ============================================================
# Test: List Houses
# ============================================================

@pytest.mark.anyio
class TestListHouses:
    """Test GET /api/resident/houses"""
    
    async def test_list_houses_unauthorized(self, client):
        """Should return 401 without login"""
        response = await client.get("/api/resident/houses")
        assert response.status_code == 401
    
    async def test_list_houses_after_login(self, client, reset_otp_store):
        """Should return empty list for new user (no memberships)"""
        cookies = await login_resident(client)
        
        response = await client.get(
            "/api/resident/houses",
            cookies=cookies
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "houses" in data
        # New user has no memberships
        assert isinstance(data["houses"], list)


# ============================================================
# Test: Select House
# ============================================================

@pytest.mark.anyio
class TestSelectHouse:
    """Test POST /api/resident/select-house"""
    
    async def test_select_house_unauthorized(self, client):
        """Should return 401 without login"""
        response = await client.post(
            "/api/resident/select-house",
            json={"house_id": 1}
        )
        assert response.status_code == 401
    
    async def test_select_house_invalid_membership(self, client, reset_otp_store):
        """Should return 403 for house without membership"""
        cookies = await login_resident(client)
        
        response = await client.post(
            "/api/resident/select-house",
            json={"house_id": 99999},  # Non-existent/unauthorized house
            cookies=cookies
        )
        
        assert response.status_code == 403
        assert "ไม่มีสิทธิ์" in response.json()["detail"]
    
    async def test_select_house_validation_error(self, client, reset_otp_store):
        """Should return 422 for invalid house_id"""
        cookies = await login_resident(client)
        
        response = await client.post(
            "/api/resident/select-house",
            json={"house_id": 0},  # Invalid (must be > 0)
            cookies=cookies
        )
        
        assert response.status_code == 422


# ============================================================
# Test: Switch House
# ============================================================

@pytest.mark.anyio
class TestSwitchHouse:
    """Test POST /api/resident/switch-house"""
    
    async def test_switch_house_unauthorized(self, client):
        """Should return 401 without login"""
        response = await client.post(
            "/api/resident/switch-house",
            json={"house_id": 1}
        )
        assert response.status_code == 401
    
    async def test_switch_house_invalid_membership(self, client, reset_otp_store):
        """Should return 403 for house without membership"""
        cookies = await login_resident(client)
        
        response = await client.post(
            "/api/resident/switch-house",
            json={"house_id": 99999},
            cookies=cookies
        )
        
        assert response.status_code == 403


# ============================================================
# Test: Me With Context
# ============================================================

@pytest.mark.anyio
class TestMeWithContext:
    """Test GET /api/resident/me/context"""
    
    async def test_me_context_unauthorized(self, client):
        """Should return 401 without login"""
        response = await client.get("/api/resident/me/context")
        assert response.status_code == 401
    
    async def test_me_context_after_login(self, client, reset_otp_store):
        """Should return user info with no active house initially"""
        cookies = await login_resident(client)
        
        response = await client.get(
            "/api/resident/me/context",
            cookies=cookies
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] is not None
        assert data["active_house_id"] is None  # No house selected yet
        assert data["active_house_code"] is None


# ============================================================
# Unit Tests: Token Payload
# ============================================================

class TestTokenPayload:
    """Test token payload structure"""
    
    def test_token_without_house(self):
        """Initial token should not have house_id"""
        from app.core.auth import create_access_token, verify_token
        
        token_data = {
            "sub": "123",
            "role": "resident"
        }
        
        token = create_access_token(data=token_data)
        payload = verify_token(token)
        
        assert payload is not None
        # verify_token returns "user_id" from "sub" (keeps as string)
        assert payload.get("user_id") == "123"
        assert payload.get("role") == "resident"
        assert payload.get("house_id") is None  # verify_token returns "house_id" key
    
    def test_token_with_house(self):
        """Token after select should have house_id"""
        from app.core.auth import create_access_token, verify_token
        
        token_data = {
            "sub": "123",
            "role": "resident",
            "house_id": 45  # JWT payload uses house_id
        }
        
        token = create_access_token(data=token_data)
        payload = verify_token(token)
        
        assert payload is not None
        # verify_token returns "user_id" from "sub" (keeps as string)
        assert payload.get("user_id") == "123"
        assert payload.get("role") == "resident"
        assert payload.get("house_id") == 45  # verify_token extracts house_id


# ============================================================
# Integration Test: Full Flow
# ============================================================

@pytest.mark.anyio
class TestFullFlow:
    """Test complete resident house selection flow"""
    
    async def test_login_and_check_context(self, client, reset_otp_store):
        """
        Full flow test:
        1. Login resident
        2. Check context (no house)
        3. List houses (empty for new user)
        """
        # 1. Login
        cookies = await login_resident(client)
        
        # 2. Check context - no house selected
        response = await client.get(
            "/api/resident/me/context",
            cookies=cookies
        )
        assert response.status_code == 200
        data = response.json()
        assert data["active_house_id"] is None
        
        # 3. List houses
        response = await client.get(
            "/api/resident/houses",
            cookies=cookies
        )
        assert response.status_code == 200
        data = response.json()
        assert "houses" in data


# ============================================================
# Security Tests
# ============================================================

@pytest.mark.anyio
class TestSecurityRules:
    """Test security rules from R.3 spec"""
    
    async def test_house_id_not_from_query_param(self, client, reset_otp_store):
        """house_id should NOT come from query params"""
        cookies = await login_resident(client)
        
        # Try to access with house_id in query (should be ignored)
        response = await client.get(
            "/api/resident/me/context?house_id=99999",
            cookies=cookies
        )
        
        # Should still work, but house_id from query is ignored
        assert response.status_code == 200
        data = response.json()
        # active_house_id comes from token, not query
        assert data["active_house_id"] is None
    
    async def test_client_cannot_set_active_house_directly(self, client, reset_otp_store):
        """Client cannot set active_house via custom headers"""
        cookies = await login_resident(client)
        
        # Try with custom header
        response = await client.get(
            "/api/resident/me/context",
            cookies=cookies,
            headers={"X-Active-House-Id": "99999"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # active_house_id comes from token only
        assert data["active_house_id"] is None


# ============================================================
# Accounting Non-Impact Test
# ============================================================

@pytest.mark.anyio
class TestAccountingNonImpact:
    """Verify accounting endpoints are not affected"""
    
    async def test_accounting_endpoints_unchanged(self, client):
        """Accounting endpoints should work independently"""
        # These should return 401 (auth required) or 200 (if public), not 500 (broken)
        endpoints = [
            "/api/invoices",
        ]
        
        for endpoint in endpoints:
            response = await client.get(endpoint)
            # Should not be 500 (server error)
            assert response.status_code != 500, f"Endpoint {endpoint} broken"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
