"""
Phase D.3: SMSMKT OTP Provider

Production OTP provider using SMSMKT.com API.

API Documentation:
- Send OTP: POST https://portal-otp.smsmkt.com/api/otp-send
- Validate OTP: POST https://portal-otp.smsmkt.com/api/otp-validate

Required Environment Variables:
- SMSMKT_API_KEY
- SMSMKT_SECRET_KEY
- SMSMKT_PROJECT_KEY
"""
import os
import logging
from typing import Optional
import httpx

from .base import OTPProvider, OTPSendResult, OTPValidateResult

logger = logging.getLogger(__name__)


class SMSMKTProvider(OTPProvider):
    """
    SMSMKT.com OTP provider for production.
    
    Endpoints:
    - POST /api/otp-send - Send OTP SMS
    - POST /api/otp-validate - Validate OTP code
    """
    
    BASE_URL = "https://portal-otp.smsmkt.com/api"
    
    def __init__(self):
        self.api_key = os.getenv("SMSMKT_API_KEY", "")
        self.secret_key = os.getenv("SMSMKT_SECRET_KEY", "")
        self.project_key = os.getenv("SMSMKT_PROJECT_KEY", "")
        
        # HTTP client with timeout
        self.timeout = httpx.Timeout(30.0, connect=10.0)
    
    @property
    def provider_name(self) -> str:
        return "smsmkt"
    
    def _get_headers(self) -> dict:
        """Get headers for SMSMKT API requests"""
        return {
            "Content-Type": "application/json",
            "api_key": self.api_key,
            "secret_key": self.secret_key
        }
    
    def send_otp(self, phone: str, ref_code: Optional[str] = None) -> OTPSendResult:
        """
        Send OTP via SMSMKT API.
        
        API: POST /api/otp-send
        Request: { project_key, phone, ref_code }
        Response: { result_code, token, ref_code, ... }
        """
        url = f"{self.BASE_URL}/otp-send"
        
        payload = {
            "project_key": self.project_key,
            "phone": phone
        }
        if ref_code:
            payload["ref_code"] = ref_code
        
        masked_phone = f"***{phone[-4:]}" if len(phone) >= 4 else "****"
        logger.info(f"[SMSMKT] Sending OTP to {masked_phone}")
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
                
                data = response.json()
                logger.debug(f"[SMSMKT] send_otp response: {data}")
                
                # Check response
                if response.status_code == 200 and data.get("result_code") == "200":
                    return OTPSendResult(
                        success=True,
                        token=data.get("token"),
                        ref_code=data.get("ref_code")
                    )
                else:
                    error_msg = data.get("developer_message") or data.get("message") or "Unknown error"
                    logger.error(f"[SMSMKT] send_otp failed: {error_msg}")
                    return OTPSendResult(
                        success=False,
                        error_message=f"ส่ง OTP ไม่สำเร็จ: {error_msg}",
                        error_code=data.get("result_code", "UNKNOWN")
                    )
                    
        except httpx.TimeoutException:
            logger.error("[SMSMKT] send_otp timeout")
            return OTPSendResult(
                success=False,
                error_message="ระบบ SMS ไม่ตอบสนอง กรุณาลองใหม่อีกครั้ง",
                error_code="TIMEOUT"
            )
        except httpx.HTTPError as e:
            logger.error(f"[SMSMKT] send_otp HTTP error: {e}")
            return OTPSendResult(
                success=False,
                error_message="เกิดข้อผิดพลาดในการส่ง OTP",
                error_code="HTTP_ERROR"
            )
        except Exception as e:
            logger.exception(f"[SMSMKT] send_otp unexpected error: {e}")
            return OTPSendResult(
                success=False,
                error_message="เกิดข้อผิดพลาดไม่ทราบสาเหตุ",
                error_code="UNKNOWN_ERROR"
            )
    
    def validate_otp(
        self,
        phone: str,
        otp_code: str,
        token: Optional[str] = None,
        ref_code: Optional[str] = None
    ) -> OTPValidateResult:
        """
        Validate OTP via SMSMKT API.
        
        API: POST /api/otp-validate
        Request: { token, otp_code, ref_code }
        Response: { result_code, status, ... }
        """
        if not token:
            return OTPValidateResult(
                success=False,
                error_message="ไม่พบ token สำหรับยืนยัน OTP",
                error_code="MISSING_TOKEN"
            )
        
        url = f"{self.BASE_URL}/otp-validate"
        
        payload = {
            "token": token,
            "otp_code": otp_code
        }
        if ref_code:
            payload["ref_code"] = ref_code
        
        masked_phone = f"***{phone[-4:]}" if len(phone) >= 4 else "****"
        logger.info(f"[SMSMKT] Validating OTP for {masked_phone}")
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
                
                data = response.json()
                logger.debug(f"[SMSMKT] validate_otp response: {data}")
                
                # Check response - status=true means OTP is valid
                if response.status_code == 200 and data.get("status") == True:
                    return OTPValidateResult(success=True)
                else:
                    # Try to get meaningful error message
                    error_msg = data.get("developer_message") or data.get("message") or "OTP ไม่ถูกต้อง"
                    result_code = data.get("result_code", "INVALID")
                    
                    # Map common SMSMKT error codes
                    if result_code == "400":
                        error_msg = "OTP ไม่ถูกต้อง"
                    elif result_code == "401":
                        error_msg = "OTP หมดอายุ"
                    elif result_code == "404":
                        error_msg = "ไม่พบ OTP กรุณาขอใหม่"
                    
                    return OTPValidateResult(
                        success=False,
                        error_message=error_msg,
                        error_code=result_code
                    )
                    
        except httpx.TimeoutException:
            logger.error("[SMSMKT] validate_otp timeout")
            return OTPValidateResult(
                success=False,
                error_message="ระบบ SMS ไม่ตอบสนอง กรุณาลองใหม่",
                error_code="TIMEOUT"
            )
        except httpx.HTTPError as e:
            logger.error(f"[SMSMKT] validate_otp HTTP error: {e}")
            return OTPValidateResult(
                success=False,
                error_message="เกิดข้อผิดพลาดในการยืนยัน OTP",
                error_code="HTTP_ERROR"
            )
        except Exception as e:
            logger.exception(f"[SMSMKT] validate_otp unexpected error: {e}")
            return OTPValidateResult(
                success=False,
                error_message="เกิดข้อผิดพลาดไม่ทราบสาเหตุ",
                error_code="UNKNOWN_ERROR"
            )
    
    def validate_config(self) -> bool:
        """
        Validate SMSMKT configuration.
        Raises RuntimeError if required keys are missing.
        """
        missing = []
        
        if not self.api_key:
            missing.append("SMSMKT_API_KEY")
        if not self.secret_key:
            missing.append("SMSMKT_SECRET_KEY")
        if not self.project_key:
            missing.append("SMSMKT_PROJECT_KEY")
        
        if missing:
            raise RuntimeError(
                f"❌ SMSMKT Provider requires these environment variables: {', '.join(missing)}. "
                f"Get these from your SMSMKT.com dashboard."
            )
        
        logger.info("✅ SMSMKT OTP Provider configured")
        logger.info(f"   API Key: {self.api_key[:8]}...")
        logger.info(f"   Project Key: {self.project_key[:8]}...")
        
        return True
