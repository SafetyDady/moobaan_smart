"""
Phase D.3: OTP Provider Base Interface

Abstract base class for OTP providers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class OTPSendResult:
    """Result from sending OTP"""
    success: bool
    token: Optional[str] = None  # Provider token for validation (e.g., SMSMKT token)
    ref_code: Optional[str] = None  # Reference code for user display
    otp_code: Optional[str] = None  # Only set in mock mode
    error_message: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class OTPValidateResult:
    """Result from validating OTP"""
    success: bool
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class OTPProvider(ABC):
    """
    Abstract base class for OTP providers.
    
    Implementations:
    - MockOTPProvider: Fixed OTP for development
    - SMSMKTProvider: Real SMS via SMSMKT.com
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g., 'mock', 'smsmkt')"""
        pass
    
    @abstractmethod
    def send_otp(self, phone: str, ref_code: Optional[str] = None) -> OTPSendResult:
        """
        Send OTP to phone number.
        
        Args:
            phone: Normalized Thai mobile number (e.g., "0812345678")
            ref_code: Optional reference code for tracking
            
        Returns:
            OTPSendResult with success status and provider-specific data
        """
        pass
    
    @abstractmethod
    def validate_otp(
        self, 
        phone: str, 
        otp_code: str, 
        token: Optional[str] = None,
        ref_code: Optional[str] = None
    ) -> OTPValidateResult:
        """
        Validate OTP code.
        
        Args:
            phone: Normalized Thai mobile number
            otp_code: User-entered OTP code
            token: Provider token from send_otp (required for some providers)
            ref_code: Reference code (optional)
            
        Returns:
            OTPValidateResult with success status
        """
        pass
    
    def validate_config(self) -> bool:
        """
        Validate provider configuration at startup.
        Should raise RuntimeError if configuration is invalid.
        
        Returns:
            True if configuration is valid
        """
        return True
