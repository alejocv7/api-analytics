from app.core import security
from app.core.config import settings


def test_hash_ip():
    ip = "192.168.1.1"
    salt = "test-salt"
    hashed = security.hash_ip(ip, salt)

    assert hashed is not None
    assert len(hashed) == 16
    assert security.hash_ip(ip, salt) == hashed
    assert security.hash_ip("192.168.1.2", salt) != hashed
    assert security.hash_ip(None, salt) is None


def test_generate_api_key():
    full_key, prefix, hashed = security.generate_api_key()

    assert full_key.startswith(settings.API_KEY_PREFIX)
    assert len(full_key) == len(settings.API_KEY_PREFIX) + settings.API_KEY_LENGTH
    assert prefix == full_key[: settings.API_KEY_LOOKUP_PREFIX_LENGTH]
    assert security.compare_api_key(full_key, hashed) is True


def test_password_hashing():
    password = "MySecurePassword123!"
    hashed = security.hash_password(password)

    assert hashed != password

    match, new_hash = security.verify_password(password, hashed)
    assert match is True
    assert new_hash is None or isinstance(new_hash, str)

    match, _ = security.verify_password("wrong-password", hashed)
    assert match is False
