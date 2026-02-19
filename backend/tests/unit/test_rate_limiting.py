"""Unit tests for rate limiting key functions and configuration."""

from types import SimpleNamespace

from app.core import rate_limits
from app.core.rate_limiter import get_project_key, get_user_key


class MockUser:
    """Mock user object for testing."""

    def __init__(self, user_id: int):
        self.id = user_id


class MockRequest:
    """Mock request object for testing."""

    def __init__(self) -> None:
        self.state = SimpleNamespace()
        self.client = SimpleNamespace(host="127.0.0.1")


def test_get_user_key_with_user():
    """Test get_user_key returns user-based key when user is set."""
    request = MockRequest()
    request.state.user = MockUser(42)

    key = get_user_key(request)  # type: ignore[arg-type]

    assert key == "user:42"


def test_get_user_key_without_user():
    """Test get_user_key falls back to IP when user is not set."""
    request = MockRequest()

    key = get_user_key(request)  # type: ignore[arg-type]

    assert key == "127.0.0.1"


def test_get_user_key_with_none_user():
    """Test get_user_key falls back to IP when user is None."""
    request = MockRequest()
    request.state.user = None

    key = get_user_key(request)  # type: ignore[arg-type]

    assert key == "127.0.0.1"


def test_get_project_key_with_project():
    """Test get_project_key returns project-based key when project_id is set."""
    request = MockRequest()
    request.state.project_id = 123

    key = get_project_key(request)  # type: ignore[arg-type]

    assert key == "project:123"


def test_get_project_key_without_project():
    """Test get_project_key falls back to IP when project_id is not set."""
    request = MockRequest()

    key = get_project_key(request)  # type: ignore[arg-type]

    assert key == "127.0.0.1"


def test_get_project_key_with_none_project():
    """Test get_project_key falls back to IP when project_id is None."""
    request = MockRequest()
    request.state.project_id = None

    key = get_project_key(request)  # type: ignore[arg-type]

    assert key == "127.0.0.1"


def test_rate_limit_constants_are_valid():
    """Test that all rate limit constants are valid slowapi format strings."""
    valid_periods = {"second", "minute", "hour", "day"}

    constants = [
        rate_limits.GLOBAL,
        rate_limits.AUTH_REGISTER,
        rate_limits.AUTH_LOGIN,
        rate_limits.TRACK,
        rate_limits.DATA_READ,
        rate_limits.DATA_WRITE,
        rate_limits.DATA_DELETE,
        rate_limits.KEY_ROTATE,
    ]

    for constant in constants:
        # Format should be "<count>/<period>"
        assert "/" in constant, f"Invalid format: {constant}"
        count, period = constant.split("/")
        assert count.isdigit(), f"Count must be numeric: {constant}"
        assert period in valid_periods, f"Invalid period: {constant}"
