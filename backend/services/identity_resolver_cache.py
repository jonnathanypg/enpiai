"""
Identity Resolver Cache Service - High Performance Hash Map Engine (O(1) Lookup)
Caches WhatsApp Phone Number resolution (59398...), multi-tenant tenant_id mapping,
and Fernet PII Encryption Key references in memory with TTL.

Zero-Downtime & Non-Destructive: Operates as an acceleration layer without altering DB tables.
"""
import time
from typing import Dict, Any, Optional, Tuple

class IdentityHashMapCache:
    """
    In-Memory Hash Map Cache for Phone Resolution & Multi-Tenant Scoping (O(1))
    """
    _cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
    _TTL_SECONDS: int = 300  # 5 minutes TTL

    @classmethod
    def get_phone_identity(cls, phone_number: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached phone identity in O(1) time"""
        if not phone_number:
            return None
        
        clean_phone = phone_number.replace("+", "").replace(" ", "").strip()
        now = time.time()
        
        if clean_phone in cls._cache:
            timestamp, data = cls._cache[clean_phone]
            if now - timestamp < cls._TTL_SECONDS:
                print(f"[IdentityHashMapCache HIT O(1)]: {clean_phone[:8]}...")
                return data
            else:
                del cls._cache[clean_phone]
        return None

    @classmethod
    def set_phone_identity(cls, phone_number: str, identity_data: Dict[str, Any]):
        """Cache phone identity mapping in O(1) time"""
        if phone_number and identity_data:
            clean_phone = phone_number.replace("+", "").replace(" ", "").strip()
            cls._cache[clean_phone] = (time.time(), identity_data)

    @classmethod
    def invalidate_phone(cls, phone_number: str):
        """Invalidate a specific phone number from cache"""
        clean_phone = phone_number.replace("+", "").replace(" ", "").strip()
        if clean_phone in cls._cache:
            del cls._cache[clean_phone]

    @classmethod
    def clear_all(cls):
        """Clear entire cache"""
        cls._cache.clear()
