from app.core.config import settings
from app.services.project_service import _generate_project_key


def test_generate_project_key_format():
    name = "My Awesome Project"
    key = _generate_project_key(name)

    # Format: name-in-lower-case-with-hyphens-suffix
    assert key.startswith("my-awesome-project-")

    # Suffix length check (hex token)
    suffix_part = key.replace("my-awesome-project-", "")
    assert len(suffix_part) == settings.PROJECT_SUFFIX_LENGTH * 2


def test_generate_project_key_uniqueness():
    name = "duplicate"
    key1 = _generate_project_key(name)
    key2 = _generate_project_key(name)

    assert key1 != key2


def test_generate_project_key_special_chars():
    name = "Project! With @ Special # Chars"
    key = _generate_project_key(name)

    # Current implementation only does lower() and replace(" ", "-"). If it was
    # more robust, it would strip special chars, but let's test current behavior
    assert "project!-with-@-special-#-chars-" in key
