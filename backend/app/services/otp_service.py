"""
Phase R.2: OTP Service (Mock Mode)

Purpose:
- Generate and verify OTP for resident login
- Mock mode for development (fixed OTP: 123456)
- Security guards to prevent mock OTP in production

IMPORTANT:
- NO SMS integration
- NO accounting logic
- Mock mode ONLY
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from threading import Lock

from app.core.config import settings

logger = logging.getLogger(__name__)


# --- Configuration ---

class OTPConfig:
    """OTP Configuration with production guards"""
    
    # Mode: "mock" or "production"
    MODE: str = os.getenv("OTP_MODE", "mock")
    
    # Mock OTP code (only used if MODE == "mock")
    MOCK_CODE: str = os.getenv("OTP_MOCK_CODE", "123456")
    
    # Expiry in seconds (5 minutes)
    EXPIRY_SECONDS: int = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))
    
    # Max verification attempts per OTP
    MAX_ATTEMPTS: int = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
    
    # Rate limit: max OTP requests per phone per minute
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("OTP_RATE_LIMIT", "3"))
    
    @classmethod
    def validate(cls):
        """
        Validate configuration - FAIL if mock in production (unless explicitly overridden).
        
        Security Policy:
        - By default: ENV=production + OTP_MODE=mock → RuntimeError
        - Override: Set ALLOW_MOCK_OTP_IN_PROD=true to temporarily allow mock OTP
        
        WARNING: ALLOW_MOCK_OTP_IN_PROD should be removed once SMS gateway is configured!
        """
        env = settings.ENV.lower()
        is_production = env in ["production", "prod"]
        is_mock_mode = cls.MODE == "mock"
        allow_mock_override = os.getenv("ALLOW_MOCK_OTP_IN_PROD", "").lower() == "true"
        
        if is_production and is_mock_mode:
            if not allow_mock_override:
                raise RuntimeError(
                    "❌ SECURITY ERROR: Mock OTP not allowed in production! "
                    "Set OTP_MODE=production and configure SMS gateway. "
                    "Or set ALLOW_MOCK_OTP_IN_PROD=true to temporarily override (NOT RECOMMENDED)."
                )
            else:
                logger.warning("=" * 60)
                logger.warning("⚠️  SECURITY WARNING: Mock OTP enabled in PRODUCTION!")
                logger.warning("⚠️  This is a TEMPORARY override via ALLOW_MOCK_OTP_IN_PROD=true")
                logger.warning("⚠️  Remove this flag once SMS gateway is configured!")
                logger.warning("=" * 60)
        
        if is_mock_mode:
            logger.warning(f"⚠️ OTP Mock Mode enabled - OTP code: {cls.MOCK_CODE}")
        
        return True


# Validate on import
OTPConfig.validate()


# --- In-Memory OTP Store ---

@dataclass
class OTPRecord:
    """OTP record with metadata"""
    phone: str
    code: str
    created_at: datetime
    expires_at: datetime
    attempts: int = 0
    verified: bool = False


class OTPStore:
    """
    Thread-safe in-memory OTP store.
    
    In production, replace with Redis for:
    - Distributed deployment
    - Persistence
    - Auto-expiry
    """
    
    def __init__(self):
        self._store: Dict[str, OTPRecord] = {}
        self._rate_limits: Dict[str, list] = {}  # phone -> list of request timestamps
        self._lock = Lock()
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number (remove spaces, dashes, etc.)"""
        # Remove all non-digit characters
        digits = ''.join(c for c in phone if c.isdigit())
        
        # Handle Thai phone format
        if digits.startswith('66'):
            digits = '0' + digits[2:]
        elif digits.startswith('+66'):
            digits = '0' + digits[3:]
        
        return digits
    
    def check_rate_limit(self, phone: str) -> Tuple[bool, str]:
        """
        Check if phone has exceeded rate limit.
        Returns (allowed, message)
        """
        phone = self._normalize_phone(phone)
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)
        
        with self._lock:
            # Get or create rate limit list
            if phone not in self._rate_limits:
                self._rate_limits[phone] = []
            
            # Remove old entries
            self._rate_limits[phone] = [
                ts for ts in self._rate_limits[phone]
                if ts > one_minute_ago
            ]
            
            # Check limit
            if len(self._rate_limits[phone]) >= OTPConfig.RATE_LIMIT_PER_MINUTE:
                return False, f"กรุณารอสักครู่ ขอ OTP ได้ไม่เกิน {OTPConfig.RATE_LIMIT_PER_MINUTE} ครั้งต่อนาที"
            
            # Record this request
            self._rate_limits[phone].append(now)
            return True, ""
    
    def create_otp(self, phone: str) -> str:
        """
        Create and store OTP for phone.
        Returns the OTP code.
        """
        phone = self._normalize_phone(phone)
        now = datetime.utcnow()
        
        # Generate OTP (mock or real)
        if OTPConfig.MODE == "mock":
            code = OTPConfig.MOCK_CODE
            logger.warning(f"[MOCK OTP] Phone: ***{phone[-4:]}, OTP: {code}")
        else:
            # TODO: Generate real random OTP and send SMS
            import secrets
            code = ''.join(str(secrets.randbelow(10)) for _ in range(6))
            logger.info(f"[OTP] Generated for phone: ***{phone[-4:]}")
        
        # Create record
        record = OTPRecord(
            phone=phone,
            code=code,
            created_at=now,
            expires_at=now + timedelta(seconds=OTPConfig.EXPIRY_SECONDS),
            attempts=0,
            verified=False
        )
        
        with self._lock:
            self._store[phone] = record
        
        return code
    
    def verify_otp(self, phone: str, code: str) -> Tuple[bool, str]:
        """
        Verify OTP for phone.
        Returns (success, message)
        """
        phone = self._normalize_phone(phone)
        now = datetime.utcnow()
        
        with self._lock:
            record = self._store.get(phone)
            
            if not record:
                return False, "ไม่พบ OTP สำหรับเบอร์นี้ กรุณาขอ OTP ใหม่"
            
            if record.verified:
                return False, "OTP นี้ถูกใช้ไปแล้ว กรุณาขอ OTP ใหม่"
            
            if now > record.expires_at:
                # Clean up expired record
                del self._store[phone]
                return False, "OTP หมดอายุ กรุณาขอ OTP ใหม่"
            
            if record.attempts >= OTPConfig.MAX_ATTEMPTS:
                # Clean up after max attempts
                del self._store[phone]
                return False, f"ใส่ OTP ผิดเกิน {OTPConfig.MAX_ATTEMPTS} ครั้ง กรุณาขอ OTP ใหม่"
            
            # Increment attempts
            record.attempts += 1
            
            if record.code != code:
                remaining = OTPConfig.MAX_ATTEMPTS - record.attempts
                return False, f"OTP ไม่ถูกต้อง (เหลือ {remaining} ครั้ง)"
            
            # Success - mark as verified
            record.verified = True
            
            # Clean up after successful verification
            del self._store[phone]
            
            return True, "ยืนยัน OTP สำเร็จ"
    
    def cleanup_expired(self):
        """Remove all expired OTP records"""
        now = datetime.utcnow()
        with self._lock:
            expired = [
                phone for phone, record in self._store.items()
                if now > record.expires_at
            ]
            for phone in expired:
                del self._store[phone]


# Global OTP store instance
otp_store = OTPStore()


# --- Service Functions ---

def request_otp(phone: str) -> Tuple[bool, str]:
    """
    Request OTP for phone number.
    Returns (success, message)
    """
    # Check rate limit
    allowed, message = otp_store.check_rate_limit(phone)
    if not allowed:
        return False, message
    
    # Create OTP
    otp_store.create_otp(phone)
    
    # In mock mode, log the OTP
    if OTPConfig.MODE == "mock":
        return True, "OTP_SENT (Mock Mode)"
    else:
        return True, "OTP_SENT"


def verify_otp(phone: str, code: str) -> Tuple[bool, str]:
    """
    Verify OTP for phone number.
    Returns (success, message)
    """
    return otp_store.verify_otp(phone, code)
