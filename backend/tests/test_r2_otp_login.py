"""
Phase R.2 Tests: OTP Service and Resident Auth API

Tests for:
1. OTP Service - mock mode, rate limiting, expiry, attempts
2. Resident Auth API - request-otp, verify-otp, me, logout
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Test OTP Service directly
from app.services.otp_service import (
    OTPConfig,
    OTPStore,
    OTPRecord,
    request_otp,
    verify_otp,
    otp_store,
)


class TestOTPConfig:
    """Test OTP configuration"""
    
    def test_mock_mode_default(self):
        """OTP should be in mock mode by default in development"""
        assert OTPConfig.MODE == "mock"
        assert OTPConfig.MOCK_CODE == "123456"
    
    def test_expiry_default(self):
        """OTP expiry should be 5 minutes (300 seconds)"""
        assert OTPConfig.EXPIRY_SECONDS == 300
    
    def test_max_attempts_default(self):
        """Max OTP attempts should be 5"""
        assert OTPConfig.MAX_ATTEMPTS == 5
    
    def test_rate_limit_default(self):
        """Rate limit should be 3 per minute"""
        assert OTPConfig.RATE_LIMIT_PER_MINUTE == 3


class TestOTPStore:
    """Test OTP store operations"""
    
    def setup_method(self):
        """Reset OTP store before each test"""
        self.store = OTPStore()
    
    def test_normalize_phone_thai_format(self):
        """Test phone normalization"""
        # Standard Thai mobile
        assert self.store._normalize_phone("0812345678") == "0812345678"
        
        # With country code
        assert self.store._normalize_phone("66812345678") == "0812345678"
        assert self.store._normalize_phone("+66812345678") == "0812345678"
        
        # With spaces and dashes
        assert self.store._normalize_phone("081-234-5678") == "0812345678"
        assert self.store._normalize_phone("081 234 5678") == "0812345678"
    
    def test_create_otp_mock_mode(self):
        """Create OTP should return mock code"""
        code = self.store.create_otp("0812345678")
        assert code == OTPConfig.MOCK_CODE
    
    def test_verify_otp_success(self):
        """Verify correct OTP"""
        phone = "0812345678"
        self.store.create_otp(phone)
        
        success, message = self.store.verify_otp(phone, OTPConfig.MOCK_CODE)
        assert success is True
        assert "สำเร็จ" in message
    
    def test_verify_otp_wrong_code(self):
        """Verify wrong OTP code"""
        phone = "0812345678"
        self.store.create_otp(phone)
        
        success, message = self.store.verify_otp(phone, "000000")
        assert success is False
        assert "ไม่ถูกต้อง" in message
    
    def test_verify_otp_no_record(self):
        """Verify OTP without requesting first"""
        success, message = self.store.verify_otp("0899999999", "123456")
        assert success is False
        assert "ไม่พบ OTP" in message
    
    def test_verify_otp_already_used(self):
        """Verify OTP that was already verified"""
        phone = "0812345678"
        self.store.create_otp(phone)
        
        # First verification succeeds
        success1, _ = self.store.verify_otp(phone, OTPConfig.MOCK_CODE)
        assert success1 is True
        
        # Second verification fails (already used/cleaned up)
        success2, message = self.store.verify_otp(phone, OTPConfig.MOCK_CODE)
        assert success2 is False
        assert "ไม่พบ OTP" in message
    
    def test_verify_otp_expired(self):
        """Verify expired OTP"""
        phone = "0812345678"
        
        # Create OTP with past expiry
        now = datetime.utcnow()
        expired_record = OTPRecord(
            phone="0812345678",
            code=OTPConfig.MOCK_CODE,
            created_at=now - timedelta(minutes=10),
            expires_at=now - timedelta(minutes=5),  # Already expired
        )
        self.store._store["0812345678"] = expired_record
        
        success, message = self.store.verify_otp(phone, OTPConfig.MOCK_CODE)
        assert success is False
        assert "หมดอายุ" in message
    
    def test_verify_otp_max_attempts(self):
        """Verify OTP exceeds max attempts"""
        phone = "0812345678"
        self.store.create_otp(phone)
        
        # Use up all attempts with wrong code (5 attempts)
        for i in range(OTPConfig.MAX_ATTEMPTS):
            success, message = self.store.verify_otp(phone, "000000")
            assert success is False
        
        # On the 6th attempt, we should get "exceeded" message and record deleted
        success, message = self.store.verify_otp(phone, "000000")
        assert success is False
        assert "ผิดเกิน" in message or "ไม่พบ OTP" in message  # Either exceeded or record deleted
    
    def test_rate_limit(self):
        """Test rate limiting"""
        phone = "0812345678"
        
        # Should allow up to RATE_LIMIT_PER_MINUTE requests
        for i in range(OTPConfig.RATE_LIMIT_PER_MINUTE):
            allowed, _ = self.store.check_rate_limit(phone)
            assert allowed is True
        
        # Next request should be blocked
        allowed, message = self.store.check_rate_limit(phone)
        assert allowed is False
        assert "รอสักครู่" in message
    
    def test_cleanup_expired(self):
        """Test cleanup of expired records"""
        # Create expired record
        now = datetime.utcnow()
        self.store._store["0811111111"] = OTPRecord(
            phone="0811111111",
            code="123456",
            created_at=now - timedelta(minutes=10),
            expires_at=now - timedelta(minutes=5),
        )
        
        # Create valid record
        self.store._store["0822222222"] = OTPRecord(
            phone="0822222222",
            code="123456",
            created_at=now,
            expires_at=now + timedelta(minutes=5),
        )
        
        # Cleanup
        self.store.cleanup_expired()
        
        # Expired should be removed, valid should remain
        assert "0811111111" not in self.store._store
        assert "0822222222" in self.store._store


class TestRequestOTP:
    """Test request_otp service function"""
    
    def setup_method(self):
        """Reset OTP store"""
        otp_store._store.clear()
        otp_store._rate_limits.clear()
    
    def test_request_otp_success(self):
        """Request OTP successfully"""
        success, message = request_otp("0812345678")
        assert success is True
        assert "OTP_SENT" in message
    
    def test_request_otp_rate_limited(self):
        """Request OTP rate limited"""
        phone = "0812345678"
        
        # Use up rate limit
        for _ in range(OTPConfig.RATE_LIMIT_PER_MINUTE):
            request_otp(phone)
        
        # Next request should fail
        success, message = request_otp(phone)
        assert success is False
        assert "รอสักครู่" in message


class TestVerifyOTP:
    """Test verify_otp service function"""
    
    def setup_method(self):
        """Reset OTP store"""
        otp_store._store.clear()
        otp_store._rate_limits.clear()
    
    def test_verify_otp_success(self):
        """Verify OTP successfully"""
        phone = "0812345678"
        request_otp(phone)
        
        success, message = verify_otp(phone, OTPConfig.MOCK_CODE)
        assert success is True
        assert "สำเร็จ" in message
    
    def test_verify_otp_wrong_code(self):
        """Verify wrong OTP"""
        phone = "0812345678"
        request_otp(phone)
        
        success, message = verify_otp(phone, "999999")
        assert success is False
        assert "ไม่ถูกต้อง" in message


# ============================================================
# API Integration Tests (require running server)
# ============================================================

import httpx
from httpx import ASGITransport

# Import FastAPI app for testing
from app.main import app


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


@pytest.mark.anyio
class TestResidentAuthAPI:
    """Test Resident Auth API endpoints"""
    
    async def test_request_otp_success(self, client):
        """POST /api/resident/login/request-otp success"""
        # Reset OTP store
        otp_store._store.clear()
        otp_store._rate_limits.clear()
        
        response = await client.post(
            "/api/resident/login/request-otp",
            json={"phone": "0812345678"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["phone_masked"] == "081****678"
        # In mock mode, should have hint
        assert data["otp_hint"] == OTPConfig.MOCK_CODE
    
    async def test_request_otp_invalid_phone(self, client):
        """POST /api/resident/login/request-otp with invalid phone"""
        response = await client.post(
            "/api/resident/login/request-otp",
            json={"phone": "123"}
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_request_otp_rate_limit(self, client):
        """POST /api/resident/login/request-otp rate limited"""
        # Reset OTP store
        otp_store._store.clear()
        otp_store._rate_limits.clear()
        
        phone = "0891111111"
        
        # Use up rate limit
        for _ in range(OTPConfig.RATE_LIMIT_PER_MINUTE):
            await client.post(
                "/api/resident/login/request-otp",
                json={"phone": phone}
            )
        
        # Next request should be rate limited
        response = await client.post(
            "/api/resident/login/request-otp",
            json={"phone": phone}
        )
        
        assert response.status_code == 429
    
    async def test_verify_otp_success(self, client):
        """POST /api/resident/login/verify-otp success"""
        # Reset OTP store
        otp_store._store.clear()
        otp_store._rate_limits.clear()
        
        phone = "0812345678"
        
        # Request OTP first
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
        data = response.json()
        assert data["success"] is True
        assert data["user_id"] is not None
        assert data["phone"] == "081****678"
        
        # Should have cookies set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
        assert "csrf_token" in response.cookies
    
    async def test_verify_otp_wrong_code(self, client):
        """POST /api/resident/login/verify-otp with wrong code"""
        # Reset OTP store
        otp_store._store.clear()
        otp_store._rate_limits.clear()
        
        phone = "0892222222"
        
        # Request OTP first
        await client.post(
            "/api/resident/login/request-otp",
            json={"phone": phone}
        )
        
        # Verify with wrong OTP
        response = await client.post(
            "/api/resident/login/verify-otp",
            json={"phone": phone, "otp": "000000"}
        )
        
        assert response.status_code == 401
    
    async def test_get_me_without_login(self, client):
        """GET /api/resident/me without login"""
        response = await client.get("/api/resident/me")
        assert response.status_code == 401
    
    async def test_get_me_after_login(self, client):
        """GET /api/resident/me after login"""
        # Reset OTP store
        otp_store._store.clear()
        otp_store._rate_limits.clear()
        
        phone = "0893333333"
        
        # Login flow
        await client.post(
            "/api/resident/login/request-otp",
            json={"phone": phone}
        )
        
        login_response = await client.post(
            "/api/resident/login/verify-otp",
            json={"phone": phone, "otp": OTPConfig.MOCK_CODE}
        )
        
        # Get cookies from login response
        cookies = login_response.cookies
        
        # Get me with cookies
        me_response = await client.get(
            "/api/resident/me",
            cookies={"access_token": cookies["access_token"]}
        )
        
        assert me_response.status_code == 200
        data = me_response.json()
        assert data["user_id"] is not None
        assert data["phone"] == "089****333"
    
    async def test_logout(self, client):
        """POST /api/resident/logout"""
        response = await client.post("/api/resident/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Cookies should be cleared (set to empty with past expiry)
        # Note: httpx may not show the cleared cookies directly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
