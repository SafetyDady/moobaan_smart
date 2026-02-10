"""
Phase D.3: Phone Number Normalization and Validation

Thai mobile phone number handling:
- Normalize to standard format (0812345678)
- Validate Thai mobile prefixes
- Reject invalid numbers
"""
import re
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


# Valid Thai mobile prefixes (after 0)
# AIS: 06, 08, 09 (some)
# DTAC: 06, 08, 09 (some)
# TRUE: 06, 08, 09 (some)
# Full list covers 06x, 08x, 09x
VALID_THAI_MOBILE_PREFIXES = {
    '06', '08', '09'
}

# More specific valid prefixes (after 0)
# 06: 061-069
# 08: 080-089
# 09: 090-099
VALID_SECOND_DIGITS = {
    '6': {'1', '2', '3', '4', '5', '6', '7', '8', '9'},  # 061-069
    '8': {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'},  # 080-089
    '9': {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'},  # 090-099
}


def normalize_thai_phone(phone: str) -> Tuple[bool, str, Optional[str]]:
    """
    Normalize Thai phone number to standard format.
    
    Accepts:
    - 0812345678 (standard)
    - 66812345678 (country code, no plus)
    - +66812345678 (country code with plus)
    - 812345678 (missing leading 0)
    
    Returns:
        (success, normalized_phone, error_message)
        
    Normalized format: 0812345678 (10 digits, starts with 0)
    """
    if not phone:
        return False, "", "กรุณากรอกเบอร์โทรศัพท์"
    
    # Remove all non-digit characters except leading +
    original = phone
    phone = phone.strip()
    
    # Handle +66 prefix
    if phone.startswith('+66'):
        phone = '0' + phone[3:]
    elif phone.startswith('66') and len(phone) == 11:
        # 66812345678 -> 0812345678
        phone = '0' + phone[2:]
    
    # Remove remaining non-digits
    phone = re.sub(r'\D', '', phone)
    
    # Handle case where leading 0 was stripped
    if len(phone) == 9 and phone[0] in ('6', '8', '9'):
        phone = '0' + phone
    
    # Validate length
    if len(phone) != 10:
        return False, original, f"เบอร์โทรศัพท์ต้องมี 10 หลัก (ได้ {len(phone)} หลัก)"
    
    # Validate starts with 0
    if not phone.startswith('0'):
        return False, original, "เบอร์โทรศัพท์ต้องขึ้นต้นด้วย 0"
    
    # Validate mobile prefix (2nd digit should be 6, 8, or 9)
    second_digit = phone[1]
    if second_digit not in ('6', '8', '9'):
        return False, original, "เบอร์โทรศัพท์มือถือต้องขึ้นต้นด้วย 06, 08 หรือ 09"
    
    # Validate 3rd digit (more specific prefix)
    third_digit = phone[2]
    if third_digit not in VALID_SECOND_DIGITS.get(second_digit, set()):
        return False, original, f"เบอร์โทรศัพท์ไม่ถูกต้อง (0{second_digit}{third_digit}... ไม่ใช่หมายเลขมือถือ)"
    
    return True, phone, None


def validate_thai_mobile(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that phone is a valid Thai mobile number.
    
    Returns:
        (is_valid, error_message)
    """
    success, _, error = normalize_thai_phone(phone)
    return success, error


def mask_phone(phone: str) -> str:
    """
    Mask phone number for display/logging.
    
    0812345678 -> 081****678
    """
    if not phone or len(phone) < 6:
        return "****"
    return f"{phone[:3]}****{phone[-3:]}"


# Simple validation without normalization
def is_valid_thai_mobile_format(phone: str) -> bool:
    """
    Quick check if phone looks like a valid Thai mobile.
    Does NOT normalize.
    """
    # Already normalized format
    if re.match(r'^0[689]\d{8}$', phone):
        return True
    return False
