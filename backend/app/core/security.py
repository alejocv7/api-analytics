import hashlib
import hmac


def hash_ip(ip: str | None, salt: str) -> str | None:
    """
    Hashes an IP address using HMAC-SHA256.
    Returns the first 16 characters of the hex digest.
    """
    if not ip:
        return None

    # Use HMAC (Hash-based Message Authentication Code)
    hash_obj = hmac.new(salt.encode(), msg=ip.encode(), digestmod=hashlib.sha256)
    return hash_obj.hexdigest()[:16]


def hash_api_key(api_key: str) -> str:
    """
    Hashes an API key using SHA256.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()
