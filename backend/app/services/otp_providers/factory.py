"""
Phase D.3: OTP Provider Factory

Creates the appropriate OTP provider based on configuration.

Environment Variables:
- OTP_PROVIDER: "mock" or "smsmkt" (default: "mock")
- ALLOW_MOCK_OTP_IN_PROD: "true" to allow mock in production
- OTP_SANDBOX_WHITELIST: comma-separated phone numbers for mock in production
"""
import os
import logging
from typing import Optional

from app.core.config import settings
from .base import OTPProvider
from .mock_provider import MockOTPProvider
from .smsmkt_provider import SMSMKTProvider

logger = logging.getLogger(__name__)

# Singleton instance
_provider_instance: Optional[OTPProvider] = None


def get_otp_provider() -> OTPProvider:
    """
    Get or create the OTP provider singleton.
    
    Provider selection:
    - OTP_PROVIDER=smsmkt → SMSMKTProvider (requires SMSMKT_* keys)
    - OTP_PROVIDER=mock → MockOTPProvider
    
    Production guards:
    - If ENV=production and OTP_PROVIDER=mock:
      - Requires ALLOW_MOCK_OTP_IN_PROD=true
      - Requires OTP_SANDBOX_WHITELIST to be set
    - If ENV=production and OTP_PROVIDER=smsmkt:
      - Requires all SMSMKT_* keys
    """
    global _provider_instance
    
    if _provider_instance is not None:
        return _provider_instance
    
    provider_type = os.getenv("OTP_PROVIDER", "mock").lower()
    env = settings.ENV.lower()
    is_production = env in ["production", "prod"]
    
    logger.info(f"🔧 Initializing OTP Provider: {provider_type} (ENV={env})")
    
    if provider_type == "smsmkt":
        provider = SMSMKTProvider()
        provider.validate_config()
        _provider_instance = provider
        
    elif provider_type == "mock":
        # Production guard for mock provider
        if is_production:
            _validate_mock_in_production()
        
        provider = MockOTPProvider()
        provider.validate_config()
        _provider_instance = provider
        
    else:
        raise RuntimeError(
            f"❌ Unknown OTP_PROVIDER: {provider_type}. "
            f"Supported: 'mock', 'smsmkt'"
        )
    
    return _provider_instance


def _validate_mock_in_production():
    """
    Validate that mock OTP is properly configured for production.
    
    Rules:
    1. ALLOW_MOCK_OTP_IN_PROD must be "true"
    2. OTP_SANDBOX_WHITELIST must be non-empty
    
    This prevents accidental deployment with mock OTP without restrictions.
    """
    allow_mock = os.getenv("ALLOW_MOCK_OTP_IN_PROD", "").lower() == "true"
    whitelist = os.getenv("OTP_SANDBOX_WHITELIST", "").strip()
    
    if not allow_mock:
        raise RuntimeError(
            "❌ SECURITY ERROR: Mock OTP not allowed in production!\n"
            "Options:\n"
            "  1. Set OTP_PROVIDER=smsmkt and configure SMSMKT_* keys\n"
            "  2. Set ALLOW_MOCK_OTP_IN_PROD=true AND OTP_SANDBOX_WHITELIST=phone1,phone2\n"
            "\n"
            "⚠️ Option 2 is for TESTING ONLY. Never use in real production!"
        )
    
    if not whitelist:
        raise RuntimeError(
            "❌ SECURITY ERROR: Mock OTP in production requires OTP_SANDBOX_WHITELIST!\n"
            "Set OTP_SANDBOX_WHITELIST=0812345678,0898765432 (comma-separated)\n"
            "Only phones in this list can use mock OTP.\n"
            "\n"
            "This prevents abuse and ensures mock OTP is limited to known test phones."
        )
    
    # Parse and log whitelist
    phones = [p.strip() for p in whitelist.split(",") if p.strip()]
    
    logger.warning("=" * 70)
    logger.warning("🚨 MOCK OTP ENABLED IN PRODUCTION - TESTING MODE")
    logger.warning("🚨 ALLOW_MOCK_OTP_IN_PROD=true")
    logger.warning(f"🚨 Whitelist ({len(phones)} phones):")
    for phone in phones:
        masked = f"{phone[:3]}****{phone[-3:]}" if len(phone) >= 6 else "****"
        logger.warning(f"🚨   - {masked}")
    logger.warning("🚨 Non-whitelisted phones will be REJECTED (403)")
    logger.warning("=" * 70)


def get_sandbox_whitelist() -> set:
    """
    Get the set of phone numbers allowed for mock OTP in production.
    
    Returns empty set if not in production sandbox mode.
    """
    whitelist_str = os.getenv("OTP_SANDBOX_WHITELIST", "").strip()
    if not whitelist_str:
        return set()
    
    phones = set()
    for phone in whitelist_str.split(","):
        normalized = normalize_phone_for_whitelist(phone.strip())
        if normalized:
            phones.add(normalized)
    
    return phones


def normalize_phone_for_whitelist(phone: str) -> str:
    """Normalize phone for whitelist comparison"""
    # Remove all non-digits
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Handle Thai format
    if digits.startswith('66') and len(digits) == 11:
        digits = '0' + digits[2:]
    elif digits.startswith('+66'):
        digits = '0' + digits[3:]
    
    return digits


def is_phone_in_sandbox_whitelist(phone: str) -> bool:
    """
    Check if phone is in the sandbox whitelist.
    
    Used to restrict mock OTP in production to specific test phones.
    """
    whitelist = get_sandbox_whitelist()
    if not whitelist:
        return False
    
    normalized = normalize_phone_for_whitelist(phone)
    return normalized in whitelist


def is_sandbox_mode() -> bool:
    """
    Check if running in production sandbox mode (mock + whitelist).
    """
    env = settings.ENV.lower()
    is_production = env in ["production", "prod"]
    provider_type = os.getenv("OTP_PROVIDER", "mock").lower()
    allow_mock = os.getenv("ALLOW_MOCK_OTP_IN_PROD", "").lower() == "true"
    
    return is_production and provider_type == "mock" and allow_mock
