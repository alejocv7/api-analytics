import pytest

from app.core.types import normalize_url_path


def test_normalize_url_path_valid():
    assert normalize_url_path("/path/to/resource") == "/path/to/resource"
    assert normalize_url_path("/path/to/resource/") == "/path/to/resource"
    assert normalize_url_path("/") == "/"


def test_normalize_url_path_invalid():
    with pytest.raises(ValueError, match="url_path must start with '/'"):
        normalize_url_path("relative/path")


def test_normalize_url_path_multiple_slashes():
    # .rstrip("/") only removes trailing slashes
    assert normalize_url_path("/path///") == "/path"
    assert normalize_url_path("///") == "/"
