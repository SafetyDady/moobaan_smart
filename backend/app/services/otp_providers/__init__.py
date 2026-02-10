"""
Phase D.3: OTP Provider Abstraction

Supports:
- mock: Fixed OTP (123456) for development/testing
- smsmkt: SMSMKT.com production OTP gateway
"""
from .base import OTPProvider, OTPSendResult, OTPValidateResult
from .mock_provider import MockOTPProvider
from .smsmkt_provider import SMSMKTProvider
from .factory import get_otp_provider

__all__ = [
    "OTPProvider",
    "OTPSendResult",
    "OTPValidateResult",
    "MockOTPProvider",
    "SMSMKTProvider",
    "get_otp_provider",
]
