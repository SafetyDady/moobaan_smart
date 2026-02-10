"""
Phase R.2 + D.1 + D.3: OTP Service with Provider Abstraction

Purpose:
- Generate and verify OTP for resident login
- Provider abstraction (mock/smsmkt)
- Production-safe mock with whitelist

Phase D.1 Hardening (preserved):
- Rate limit: 3 OTP requests per 10 minutes per phone
- Verify lock: 5 wrong attempts → 10 minute lockout
- Security logging (masked PII)

Phase D.3 Additions:
- Provider abstraction (OTP_PROVIDER env var)
- SMSMKT production provider
- Sandbox whitelist for mock in production

IMPORTANT:
- NO accounting logic
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, field
from threading import Lock

from app.core.config import settings
from app.services.phone_utils import normalize_thai_phone, mask_phone
from app.services.otp_providers import get_otp_provider
from app.services.otp_providers.factory import (
    is_sandbox_mode, 
    is_phone_in_sandbox_whitelist,
    get_sandbox_whitelist
)

logger = logging.getLogger(__name__)


# --- Configuration ---

class OTPConfig:
    """OTP Configuration with production guards and rate limits"""
    
    # Provider: "mock" or "smsmkt"
    PROVIDER: str = os.getenv("OTP_PROVIDER", "mock")
    
    # Legacy MODE for backward compatibility
    MODE: str = os.getenv("OTP_MODE", os.getenv("OTP_PROVIDER", "mock"))
    
    # Mock OTP code (only used if PROVIDER == "mock")
    MOCK_CODE: str = os.getenv("OTP_MOCK_CODE", "123456")
    
    # Expiry in seconds (5 minutes)
    EXPIRY_SECONDS: int = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))
    
    # Max verification attempts per OTP (before requiring new OTP)
    MAX_ATTEMPTS: int = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
    
    # --- Phase D.1: Rate Limiting Config ---
    RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv("OTP_RATE_LIMIT_MAX", "3"))
    RATE_LIMIT_WINDOW_MINUTES: int = int(os.getenv("OTP_RATE_LIMIT_WINDOW", "10"))
    
    # Verify lockout: wrong attempts trigger lockout
    VERIFY_LOCKOUT_ATTEMPTS: int = int(os.getenv("OTP_VERIFY_LOCKOUT_ATTEMPTS", "5"))
    VERIFY_LOCKOUT_MINUTES: int = int(os.getenv("OTP_VERIFY_LOCKOUT_MINUTES", "10"))
    
    # Legacy (kept for backward compatibility)
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("OTP_RATE_LIMIT", "3"))
    
    @classmethod
    def validate(cls):
        """
        Validate configuration at startup.
        
        Phase D.3: Provider-based validation
        - Provider initialization handles security guards
        - This just logs configuration
        """
        # Initialize provider (this validates configuration)
        try:
            provider = get_otp_provider()
            cls.PROVIDER = provider.provider_name
            cls.MODE = provider.provider_name  # Keep MODE in sync for backward compat
        except RuntimeError as e:
            # Re-raise with clear message
            raise
        
        # Log configuration
        if cls.PROVIDER == "mock":
            logger.warning(f"⚠️ OTP Mock Mode enabled - fixed OTP code: {cls.MOCK_CODE}")
        
        logger.info(f"📊 OTP Rate Limits: {cls.RATE_LIMIT_MAX_REQUESTS} requests / {cls.RATE_LIMIT_WINDOW_MINUTES} min")
        logger.info(f"📊 OTP Verify Lock: {cls.VERIFY_LOCKOUT_ATTEMPTS} wrong attempts → {cls.VERIFY_LOCKOUT_MINUTES} min lockout")
        
        return True


# --- Security Logging Helper ---

def _mask_phone(phone: str) -> str:
    """Mask phone number for logging: 081****678"""
    return mask_phone(phone)


def _log_otp_event(action: str, phone: str, result: str, extra: dict = None):
    """
    Phase D.1: Security audit logging for OTP events
    Logs masked phone, action, result, timestamp
    """
    masked = _mask_phone(phone)
    log_data = {
        "action": action,
        "phone_masked": masked,
        "result": result,
        "timestamp": datetime.utcnow().isoformat()
    }
    if extra:
        log_data.update(extra)
    
    # Log as INFO for successful events, WARNING for failures
    if result in ["success", "sent"]:
        logger.info(f"[OTP_AUDIT] {action}: {result} | phone={masked}")
    else:
        logger.warning(f"[OTP_AUDIT] {action}: {result} | phone={masked} | {extra or ''}")


# --- Sandbox Whitelist Check ---

def check_sandbox_whitelist(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Check if phone is allowed in sandbox mode.
    
    Returns:
        (allowed, error_message)
        
    In sandbox mode (production + mock), only whitelisted phones are allowed.
    In other modes, all phones are allowed.
    """
    if not is_sandbox_mode():
        return True, None
    
    if is_phone_in_sandbox_whitelist(phone):
        return True, None
    
    masked = _mask_phone(phone)
    logger.warning(f"[OTP_SANDBOX] Rejected non-whitelisted phone: {masked}")
    
    return False, "OTP_SANDBOX_ONLY"


# --- In-Memory OTP Store ---

@dataclass
class OTPRecord:
    """OTP record with metadata"""
    phone: str
    code: str  # For mock provider; empty for smsmkt
    token: Optional[str] = None  # Provider token (for smsmkt validation)
    ref_code: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(seconds=300))
    attempts: int = 0
    verified: bool = False


@dataclass 
class VerifyLockRecord:
    """Phase D.1: Track verify failures for lockout"""
    phone: str
    fail_count: int = 0
    first_fail_at: Optional[datetime] = None
    locked_until: Optional[datetime] = None


class OTPStore:
    """
    Thread-safe in-memory OTP store with Phase D.1 hardening.
    
    Phase D.3: Now stores provider tokens for SMSMKT validation.
    
    Rate Limiting:
    - Request OTP: 3 times per 10 minutes per phone
    - Verify lockout: 5 wrong attempts → 10 minute lock
    
    In production, consider Redis for:
    - Distributed deployment
    - Persistence across restarts
    - Auto-expiry
    """
    
    def __init__(self):
        self._store: Dict[str, OTPRecord] = {}
        self._rate_limits: Dict[str, list] = {}  # phone -> list of request timestamps
        self._verify_locks: Dict[str, VerifyLockRecord] = {}  # Phase D.1: verify failure tracking
        self._lock = Lock()
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number using phone_utils"""
        valid, normalized, _ = normalize_thai_phone(phone)
        return normalized if valid else phone
    
    def check_rate_limit(self, phone: str) -> Tuple[bool, str]:
        """
        Phase D.1: Check if phone has exceeded rate limit.
        Policy: 3 requests per 10 minutes
        Returns (allowed, message)
        """
        phone = self._normalize_phone(phone)
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=OTPConfig.RATE_LIMIT_WINDOW_MINUTES)
        
        with self._lock:
            # Get or create rate limit list
            if phone not in self._rate_limits:
                self._rate_limits[phone] = []
            
            # Remove entries outside the window
            self._rate_limits[phone] = [
                ts for ts in self._rate_limits[phone]
                if ts > window_start
            ]
            
            # Check limit
            if len(self._rate_limits[phone]) >= OTPConfig.RATE_LIMIT_MAX_REQUESTS:
                # Calculate wait time
                oldest = min(self._rate_limits[phone])
                wait_seconds = int((oldest + timedelta(minutes=OTPConfig.RATE_LIMIT_WINDOW_MINUTES) - now).total_seconds())
                wait_minutes = max(1, (wait_seconds + 59) // 60)
                
                _log_otp_event("request_otp", phone, "rate_limited", {"wait_minutes": wait_minutes})
                
                return False, f"กรุณารอ {wait_minutes} นาที ขอ OTP ได้ไม่เกิน {OTPConfig.RATE_LIMIT_MAX_REQUESTS} ครั้ง / {OTPConfig.RATE_LIMIT_WINDOW_MINUTES} นาที"
            
            # Record this request
            self._rate_limits[phone].append(now)
            return True, ""
    
    def check_verify_lock(self, phone: str) -> Tuple[bool, str]:
        """
        Phase D.1: Check if phone is locked due to too many wrong verify attempts.
        Policy: 5 wrong attempts → 10 minute lockout
        Returns (allowed, message)
        """
        phone = self._normalize_phone(phone)
        now = datetime.utcnow()
        
        with self._lock:
            lock_record = self._verify_locks.get(phone)
            if not lock_record:
                return True, ""
            
            # Check if currently locked
            if lock_record.locked_until and now < lock_record.locked_until:
                wait_seconds = int((lock_record.locked_until - now).total_seconds())
                wait_minutes = max(1, (wait_seconds + 59) // 60)
                
                _log_otp_event("verify_otp", phone, "locked", {"wait_minutes": wait_minutes})
                
                return False, f"กรอก OTP ผิดหลายครั้ง กรุณารอ {wait_minutes} นาที"
            
            # Reset if lock has expired
            if lock_record.locked_until and now >= lock_record.locked_until:
                del self._verify_locks[phone]
            
            return True, ""
    
    def record_verify_failure(self, phone: str):
        """Phase D.1: Record a failed verify attempt, may trigger lockout"""
        phone = self._normalize_phone(phone)
        now = datetime.utcnow()
        
        with self._lock:
            if phone not in self._verify_locks:
                self._verify_locks[phone] = VerifyLockRecord(
                    phone=phone,
                    fail_count=1,
                    first_fail_at=now
                )
            else:
                self._verify_locks[phone].fail_count += 1
            
            lock_record = self._verify_locks[phone]
            
            # Check if should lock
            if lock_record.fail_count >= OTPConfig.VERIFY_LOCKOUT_ATTEMPTS:
                lock_record.locked_until = now + timedelta(minutes=OTPConfig.VERIFY_LOCKOUT_MINUTES)
                _log_otp_event("verify_otp", phone, "lockout_triggered", {
                    "fail_count": lock_record.fail_count,
                    "locked_minutes": OTPConfig.VERIFY_LOCKOUT_MINUTES
                })
    
    def clear_verify_failures(self, phone: str):
        """Phase D.1: Clear verify failures on successful verification"""
        phone = self._normalize_phone(phone)
        with self._lock:
            if phone in self._verify_locks:
                del self._verify_locks[phone]
    
    def store_otp(self, phone: str, code: str, token: Optional[str], ref_code: Optional[str]):
        """Store OTP record - Phase D.3: Called by service functions with provider results"""
        phone = self._normalize_phone(phone)
        now = datetime.utcnow()
        
        record = OTPRecord(
            phone=phone,
            code=code,
            token=token,
            ref_code=ref_code,
            created_at=now,
            expires_at=now + timedelta(seconds=OTPConfig.EXPIRY_SECONDS),
            attempts=0,
            verified=False
        )
        
        with self._lock:
            self._store[phone] = record
    
    def get_otp_record(self, phone: str) -> Optional[OTPRecord]:
        """Get OTP record for phone"""
        phone = self._normalize_phone(phone)
        with self._lock:
            return self._store.get(phone)
    
    def mark_otp_verified(self, phone: str):
        """Mark OTP as verified and remove from store"""
        phone = self._normalize_phone(phone)
        with self._lock:
            if phone in self._store:
                del self._store[phone]
    
    def increment_attempts(self, phone: str) -> int:
        """Increment verify attempts, returns new count"""
        phone = self._normalize_phone(phone)
        with self._lock:
            record = self._store.get(phone)
            if record:
                record.attempts += 1
                return record.attempts
            return 0
    
    def remove_otp(self, phone: str):
        """Remove OTP record"""
        phone = self._normalize_phone(phone)
        with self._lock:
            if phone in self._store:
                del self._store[phone]
    
    def create_otp(self, phone: str) -> str:
        """
        Legacy method - kept for backward compatibility.
        Use request_otp() service function instead.
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
        
        _log_otp_event("request_otp", phone, "sent")
        return code
    
    def verify_otp(self, phone: str, code: str) -> Tuple[bool, str]:
        """
        Verify OTP for phone.
        Phase D.1: Includes lockout tracking for failed attempts.
        Returns (success, message)
        """
        phone = self._normalize_phone(phone)
        now = datetime.utcnow()
        
        with self._lock:
            record = self._store.get(phone)
            
            if not record:
                _log_otp_event("verify_otp", phone, "no_otp_found")
                return False, "ไม่พบ OTP สำหรับเบอร์นี้ กรุณาขอ OTP ใหม่"
            
            if record.verified:
                _log_otp_event("verify_otp", phone, "already_used")
                return False, "OTP นี้ถูกใช้ไปแล้ว กรุณาขอ OTP ใหม่"
            
            if now > record.expires_at:
                # Clean up expired record
                del self._store[phone]
                _log_otp_event("verify_otp", phone, "expired")
                return False, "OTP หมดอายุ กรุณาขอ OTP ใหม่"
            
            if record.attempts >= OTPConfig.MAX_ATTEMPTS:
                # Clean up after max attempts
                del self._store[phone]
                _log_otp_event("verify_otp", phone, "max_attempts_exceeded")
                return False, f"ใส่ OTP ผิดเกิน {OTPConfig.MAX_ATTEMPTS} ครั้ง กรุณาขอ OTP ใหม่"
            
            # Increment attempts
            record.attempts += 1
            
            if record.code != code:
                remaining = OTPConfig.MAX_ATTEMPTS - record.attempts
                _log_otp_event("verify_otp", phone, "wrong_code", {"attempts": record.attempts, "remaining": remaining})
                return False, f"OTP ไม่ถูกต้อง (เหลือ {remaining} ครั้ง)"
            
            # Success - mark as verified
            record.verified = True
            
            # Clean up after successful verification
            del self._store[phone]
            
            _log_otp_event("verify_otp", phone, "success")
            return True, "ยืนยัน OTP สำเร็จ"
    
    def cleanup_expired(self):
        """Remove all expired OTP records and stale lock records"""
        now = datetime.utcnow()
        with self._lock:
            # Clean expired OTPs
            expired = [
                phone for phone, record in self._store.items()
                if now > record.expires_at
            ]
            for phone in expired:
                del self._store[phone]
            
            # Clean expired locks (Phase D.1)
            expired_locks = [
                phone for phone, lock in self._verify_locks.items()
                if lock.locked_until and now > lock.locked_until
            ]
            for phone in expired_locks:
                del self._verify_locks[phone]


# Global OTP store instance
otp_store = OTPStore()


# --- Service Functions ---

def request_otp(phone: str) -> Tuple[bool, str]:
    """
    Request OTP for phone number.
    
    Phase D.3: Uses provider abstraction
    - Normalizes phone number
    - Checks sandbox whitelist in production
    - Checks rate limit
    - Sends OTP via configured provider
    
    Returns (success, message)
    """
    # Normalize phone
    valid, normalized_phone, error = normalize_thai_phone(phone)
    if not valid:
        _log_otp_event("request_otp", phone, "invalid_phone", {"error": error})
        return False, error
    
    phone = normalized_phone
    
    # Check sandbox whitelist (production mock mode)
    allowed, error = check_sandbox_whitelist(phone)
    if not allowed:
        return False, error
    
    # Check rate limit
    allowed, message = otp_store.check_rate_limit(phone)
    if not allowed:
        return False, message
    
    # Get provider and send OTP
    provider = get_otp_provider()
    result = provider.send_otp(phone)
    
    if not result.success:
        _log_otp_event("request_otp", phone, "send_failed", {"error": result.error_message})
        return False, result.error_message or "ส่ง OTP ไม่สำเร็จ"
    
    # Store OTP record
    otp_store.store_otp(
        phone=phone,
        code=result.otp_code or "",  # Only mock provider returns code
        token=result.token,
        ref_code=result.ref_code
    )
    
    _log_otp_event("request_otp", phone, "sent")
    
    if provider.provider_name == "mock":
        return True, "OTP_SENT (Mock Mode)"
    else:
        return True, "OTP_SENT"


def verify_otp(phone: str, code: str) -> Tuple[bool, str]:
    """
    Verify OTP for phone number.
    
    Phase D.3: Uses provider abstraction
    - Normalizes phone number
    - Checks sandbox whitelist
    - Checks verify lock
    - Validates via configured provider
    
    Returns (success, message)
    """
    # Normalize phone
    valid, normalized_phone, error = normalize_thai_phone(phone)
    if not valid:
        _log_otp_event("verify_otp", phone, "invalid_phone", {"error": error})
        return False, error
    
    phone = normalized_phone
    
    # Check sandbox whitelist
    allowed, error = check_sandbox_whitelist(phone)
    if not allowed:
        return False, error
    
    # Check verify lock
    allowed, message = otp_store.check_verify_lock(phone)
    if not allowed:
        return False, message
    
    # Get OTP record
    record = otp_store.get_otp_record(phone)
    
    if not record:
        _log_otp_event("verify_otp", phone, "no_otp_found")
        return False, "ไม่พบ OTP สำหรับเบอร์นี้ กรุณาขอ OTP ใหม่"
    
    if record.verified:
        _log_otp_event("verify_otp", phone, "already_used")
        return False, "OTP นี้ถูกใช้ไปแล้ว กรุณาขอ OTP ใหม่"
    
    now = datetime.utcnow()
    if now > record.expires_at:
        otp_store.remove_otp(phone)
        _log_otp_event("verify_otp", phone, "expired")
        return False, "OTP หมดอายุ กรุณาขอ OTP ใหม่"
    
    if record.attempts >= OTPConfig.MAX_ATTEMPTS:
        otp_store.remove_otp(phone)
        _log_otp_event("verify_otp", phone, "max_attempts_exceeded")
        return False, f"ใส่ OTP ผิดเกิน {OTPConfig.MAX_ATTEMPTS} ครั้ง กรุณาขอ OTP ใหม่"
    
    # Increment attempts
    otp_store.increment_attempts(phone)
    
    # Validate via provider
    provider = get_otp_provider()
    result = provider.validate_otp(
        phone=phone,
        otp_code=code,
        token=record.token,
        ref_code=record.ref_code
    )
    
    if not result.success:
        remaining = OTPConfig.MAX_ATTEMPTS - record.attempts - 1
        otp_store.record_verify_failure(phone)
        _log_otp_event("verify_otp", phone, "wrong_code", {"attempts": record.attempts + 1, "remaining": remaining})
        
        if remaining <= 0:
            otp_store.remove_otp(phone)
            return False, f"ใส่ OTP ผิดเกิน {OTPConfig.MAX_ATTEMPTS} ครั้ง กรุณาขอ OTP ใหม่"
        
        return False, f"OTP ไม่ถูกต้อง (เหลือ {remaining} ครั้ง)"
    
    # Success
    otp_store.mark_otp_verified(phone)
    otp_store.clear_verify_failures(phone)
    
    _log_otp_event("verify_otp", phone, "success")
    return True, "ยืนยัน OTP สำเร็จ"


def get_otp_config_summary() -> dict:
    """Get OTP configuration summary for diagnostics"""
    provider = get_otp_provider()
    
    summary = {
        "provider": provider.provider_name,
        "mode": OTPConfig.MODE,  # Backward compat
        "expiry_seconds": OTPConfig.EXPIRY_SECONDS,
        "rate_limit_max_requests": OTPConfig.RATE_LIMIT_MAX_REQUESTS,
        "rate_limit_window_minutes": OTPConfig.RATE_LIMIT_WINDOW_MINUTES,
        "verify_lockout_attempts": OTPConfig.VERIFY_LOCKOUT_ATTEMPTS,
        "verify_lockout_minutes": OTPConfig.VERIFY_LOCKOUT_MINUTES,
    }
    
    # Add sandbox info if applicable
    if is_sandbox_mode():
        whitelist = get_sandbox_whitelist()
        summary["sandbox_mode"] = True
        summary["sandbox_whitelist_count"] = len(whitelist)
    
    return summary


# Validate configuration on import
OTPConfig.validate()
