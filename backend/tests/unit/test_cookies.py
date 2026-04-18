from unittest.mock import patch

from fastapi import Response

from app.core.cookies import clear_session_cookie, set_session_cookie


def _cookie_attrs(response: Response) -> dict[str, str]:
    """Parse the Set-Cookie header from a Response into a dict of attributes."""
    header = response.headers.get("set-cookie", "")
    attrs: dict[str, str] = {}
    for part in header.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            attrs[k.strip().lower()] = v.strip()
        else:
            attrs[part.lower()] = ""
    return attrs


# ---------------------------------------------------------------------------
# set_session_cookie
# ---------------------------------------------------------------------------


def test_set_session_cookie_local():
    """Local env: SameSite=Lax, not Secure, no domain."""
    response = Response()
    with patch("app.core.cookies.settings") as mock_settings:
        mock_settings.cookie_secure = False
        set_session_cookie(response, "secret123", max_age=86400)

    attrs = _cookie_attrs(response)
    assert attrs.get("session") == "secret123"
    assert attrs.get("samesite") == "lax"
    assert "secure" not in attrs
    assert "httponly" in attrs
    assert attrs.get("max-age") == "86400"
    assert "domain" not in attrs


def test_set_session_cookie_prod():
    """Production: SameSite=Lax, Secure, no domain."""
    response = Response()
    with patch("app.core.cookies.settings") as mock_settings:
        mock_settings.cookie_secure = True
        set_session_cookie(response, "secret123", max_age=86400)

    attrs = _cookie_attrs(response)
    assert attrs.get("samesite") == "lax"
    assert "secure" in attrs
    assert "domain" not in attrs


# ---------------------------------------------------------------------------
# clear_session_cookie
# ---------------------------------------------------------------------------


def test_clear_session_cookie_local():
    """Local env: SameSite=Lax, not Secure, no domain."""
    response = Response()
    with patch("app.core.cookies.settings") as mock_settings:
        mock_settings.cookie_secure = False
        clear_session_cookie(response)

    attrs = _cookie_attrs(response)
    assert attrs.get("samesite") == "lax"
    assert "secure" not in attrs
    assert "domain" not in attrs


def test_clear_session_cookie_prod():
    """Production: SameSite=Lax, Secure, no domain."""
    response = Response()
    with patch("app.core.cookies.settings") as mock_settings:
        mock_settings.cookie_secure = True
        clear_session_cookie(response)

    attrs = _cookie_attrs(response)
    assert attrs.get("samesite") == "lax"
    assert "secure" in attrs
    assert "domain" not in attrs
