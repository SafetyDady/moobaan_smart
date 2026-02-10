"""
Phase D.4.1: LINE Login Service

Purpose:
- Verify LINE OAuth authorization code
- Extract line_user_id from LINE API
- Support LINE Login for resident access

LINE Login Flow:
1. Frontend redirects to LINE authorization URL
2. User authorizes in LINE
3. LINE redirects back with authorization code
4. Backend verifies code with LINE API
5. LINE API returns access_token + id_token
6. Extract line_user_id from id_token or profile API

IMPORTANT:
- NO user creation
- NO OTP
- NO phone anchor
- NO accounting logic
"""
import os
import logging
import httpx
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LINEUserProfile:
    """LINE user profile data"""
    user_id: str
    display_name: Optional[str] = None
    picture_url: Optional[str] = None


class LINEAuthConfig:
    """LINE Login configuration"""
    
    # LINE Login credentials (from environment)
    CHANNEL_ID: str = os.getenv("LINE_CHANNEL_ID", "")
    CHANNEL_SECRET: str = os.getenv("LINE_CHANNEL_SECRET", "")
    
    # LINE API endpoints
    TOKEN_URL: str = "https://api.line.me/oauth2/v2.1/token"
    PROFILE_URL: str = "https://api.line.me/v2/profile"
    VERIFY_URL: str = "https://api.line.me/oauth2/v2.1/verify"
    
    # Redirect URI (set by frontend, verified by LINE)
    # This must match exactly what's registered in LINE Developer Console
    
    @classmethod
    def validate(cls) -> Tuple[bool, Optional[str]]:
        """Validate LINE configuration"""
        if not cls.CHANNEL_ID:
            return False, "LINE_CHANNEL_ID not set"
        if not cls.CHANNEL_SECRET:
            return False, "LINE_CHANNEL_SECRET not set"
        return True, None


class LINEAuthService:
    """
    LINE OAuth authentication service.
    
    Handles:
    - Authorization code verification
    - Access token exchange
    - User profile retrieval
    """
    
    def __init__(self):
        self.config = LINEAuthConfig
        self.http_client = httpx.Client(timeout=30.0)
    
    def exchange_code_for_token(
        self, 
        code: str, 
        redirect_uri: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from LINE
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            (success, access_token, error_message)
        """
        try:
            response = self.http_client.post(
                self.config.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.config.CHANNEL_ID,
                    "client_secret": self.config.CHANNEL_SECRET,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"[LINE_AUTH] Token exchange failed: {response.status_code} - {response.text}")
                return False, None, f"LINE token exchange failed: {response.status_code}"
            
            data = response.json()
            access_token = data.get("access_token")
            
            if not access_token:
                return False, None, "No access_token in LINE response"
            
            logger.info("[LINE_AUTH] Token exchange successful")
            return True, access_token, None
            
        except httpx.RequestError as e:
            logger.error(f"[LINE_AUTH] HTTP error during token exchange: {e}")
            return False, None, f"LINE API connection error: {str(e)}"
        except Exception as e:
            logger.error(f"[LINE_AUTH] Unexpected error during token exchange: {e}")
            return False, None, f"Unexpected error: {str(e)}"
    
    def get_user_profile(self, access_token: str) -> Tuple[bool, Optional[LINEUserProfile], Optional[str]]:
        """
        Get user profile from LINE API.
        
        Args:
            access_token: Valid LINE access token
            
        Returns:
            (success, profile, error_message)
        """
        try:
            response = self.http_client.get(
                self.config.PROFILE_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"[LINE_AUTH] Profile fetch failed: {response.status_code} - {response.text}")
                return False, None, f"LINE profile fetch failed: {response.status_code}"
            
            data = response.json()
            user_id = data.get("userId")
            
            if not user_id:
                return False, None, "No userId in LINE profile response"
            
            profile = LINEUserProfile(
                user_id=user_id,
                display_name=data.get("displayName"),
                picture_url=data.get("pictureUrl"),
            )
            
            logger.info(f"[LINE_AUTH] Profile retrieved for user: {user_id[:8]}...")
            return True, profile, None
            
        except httpx.RequestError as e:
            logger.error(f"[LINE_AUTH] HTTP error during profile fetch: {e}")
            return False, None, f"LINE API connection error: {str(e)}"
        except Exception as e:
            logger.error(f"[LINE_AUTH] Unexpected error during profile fetch: {e}")
            return False, None, f"Unexpected error: {str(e)}"
    
    def verify_and_get_profile(
        self, 
        code: str, 
        redirect_uri: str
    ) -> Tuple[bool, Optional[LINEUserProfile], Optional[str]]:
        """
        Complete LINE OAuth flow: verify code and get user profile.
        
        Args:
            code: Authorization code from LINE
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            (success, profile, error_message)
        """
        # Step 1: Exchange code for token
        success, access_token, error = self.exchange_code_for_token(code, redirect_uri)
        if not success:
            return False, None, error
        
        # Step 2: Get user profile
        success, profile, error = self.get_user_profile(access_token)
        if not success:
            return False, None, error
        
        return True, profile, None


# Global service instance
_line_auth_service: Optional[LINEAuthService] = None


def get_line_auth_service() -> LINEAuthService:
    """Get or create LINE auth service singleton"""
    global _line_auth_service
    
    if _line_auth_service is None:
        # Validate configuration
        valid, error = LINEAuthConfig.validate()
        if not valid:
            logger.warning(f"[LINE_AUTH] Configuration incomplete: {error}")
            # Still create service - will fail on actual API calls
        
        _line_auth_service = LINEAuthService()
        logger.info("[LINE_AUTH] Service initialized")
    
    return _line_auth_service


def get_line_login_url(redirect_uri: str, state: str = "") -> str:
    """
    Generate LINE Login authorization URL.
    
    Args:
        redirect_uri: URL to redirect after authorization
        state: Optional state parameter for CSRF protection
        
    Returns:
        LINE authorization URL
    """
    import urllib.parse
    import secrets
    
    # LINE requires a non-empty state parameter
    if not state:
        state = secrets.token_urlsafe(16)
    
    params = {
        "response_type": "code",
        "client_id": LINEAuthConfig.CHANNEL_ID,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": "profile openid",
    }
    
    query_string = urllib.parse.urlencode(params)
    return f"https://access.line.me/oauth2/v2.1/authorize?{query_string}"
