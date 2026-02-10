"""
Phase D.3: Mock OTP Provider

Development/testing provider with fixed OTP code (default: 123456).
"""
import os
import logging
from typing import Optional

from .base import OTPProvider, OTPSendResult, OTPValidateResult

logger = logging.getLogger(__name__)


class MockOTPProvider(OTPProvider):
    """
    Mock OTP provider for development and testing.
    
    Features:
    - Fixed OTP code (configurable via OTP_MOCK_CODE)
    - No external dependencies
    - Logs OTP to console for easy testing
    """
    
    def __init__(self):
        self.mock_code = os.getenv("OTP_MOCK_CODE", "123456")
        # In-memory storage for validation (phone -> token)
        self._tokens: dict = {}
    
    @property
    def provider_name(self) -> str:
        return "mock"
    
    def send_otp(self, phone: str, ref_code: Optional[str] = None) -> OTPSendResult:
        """
        Mock send OTP - just log and return fixed code.
        
        The mock provider stores the code internally for validate_otp.
        """
        # Generate mock token (just the phone for simplicity)
        token = f"mock_token_{phone}"
        
        # Store for validation
        self._tokens[phone] = {
            "code": self.mock_code,
            "token": token,
            "ref_code": ref_code or "MOCK"
        }
        
        # Log masked phone
        masked_phone = f"***{phone[-4:]}" if len(phone) >= 4 else "****"
        logger.warning(f"[MOCK OTP] Phone: {masked_phone}, OTP: {self.mock_code}")
        
        return OTPSendResult(
            success=True,
            token=token,
            ref_code=ref_code or "MOCK",
            otp_code=self.mock_code  # Only mock provider returns actual OTP
        )
    
    def validate_otp(
        self,
        phone: str,
        otp_code: str,
        token: Optional[str] = None,
        ref_code: Optional[str] = None
    ) -> OTPValidateResult:
        """
        Mock validate OTP - check against fixed code.
        
        Note: Mock provider validates against stored code, ignoring token parameter.
        """
        stored = self._tokens.get(phone)
        
        if not stored:
            return OTPValidateResult(
                success=False,
                error_message="ไม่พบ OTP สำหรับเบอร์นี้",
                error_code="OTP_NOT_FOUND"
            )
        
        if otp_code == stored["code"]:
            # Clean up after successful validation
            del self._tokens[phone]
            return OTPValidateResult(success=True)
        else:
            return OTPValidateResult(
                success=False,
                error_message="OTP ไม่ถูกต้อง",
                error_code="INVALID_OTP"
            )
    
    def validate_config(self) -> bool:
        """Mock provider has no configuration requirements"""
        logger.info(f"📱 Mock OTP Provider initialized (code: {self.mock_code})")
        return True
