from pydantic import BaseModel

from app.core.utils import apply_update, mask_email, normalize_whitespace


class _FakeUpdate(BaseModel):
    name: str | None = None
    value: int | None = None


class _FakeModel:
    def __init__(self, name: str, value: int) -> None:
        self.name = name
        self.value = value


# ---------------------------------------------------------------------------
# apply_update
# ---------------------------------------------------------------------------


def test_apply_update_applies_only_explicitly_set_fields():
    model = _FakeModel(name="original", value=42)
    update = _FakeUpdate(name="updated")
    apply_update(model, update)  # type: ignore[arg-type]
    assert model.name == "updated"
    assert model.value == 42  # untouched


def test_apply_update_empty_update_changes_nothing():
    model = _FakeModel(name="original", value=42)
    update = _FakeUpdate()
    apply_update(model, update)  # type: ignore[arg-type]
    assert model.name == "original"
    assert model.value == 42


def test_apply_update_explicit_none_is_applied():
    model = _FakeModel(name="original", value=42)
    update = _FakeUpdate(name=None)
    apply_update(model, update)  # type: ignore[arg-type]
    assert model.name is None
    assert model.value == 42  # untouched


def test_apply_update_all_fields():
    model = _FakeModel(name="original", value=42)
    update = _FakeUpdate(name="new", value=99)
    apply_update(model, update)  # type: ignore[arg-type]
    assert model.name == "new"
    assert model.value == 99


# ---------------------------------------------------------------------------
# mask_email
# ---------------------------------------------------------------------------


def test_mask_email_standard():
    assert mask_email("alice@example.com") == "a***e@example.com"


def test_mask_email_short_username_two_chars():
    assert mask_email("ab@example.com") == "*@example.com"


def test_mask_email_short_username_one_char():
    assert mask_email("a@example.com") == "*@example.com"


def test_mask_email_three_char_username():
    assert mask_email("abc@example.com") == "a***c@example.com"


def test_mask_email_no_at_sign():
    assert mask_email("invalid-email") == "***"


def test_mask_email_empty_string():
    assert mask_email("") == "***"


# ---------------------------------------------------------------------------
# Regression: edge cases that relied on the fixed except (ValueError, IndexError)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# normalize_whitespace
# ---------------------------------------------------------------------------


def test_normalize_whitespace_strips_leading_trailing():
    assert normalize_whitespace("  hello  ") == "hello"


def test_normalize_whitespace_collapses_internal_spaces():
    assert normalize_whitespace("hello   world") == "hello world"


def test_normalize_whitespace_collapses_tabs_and_newlines():
    assert normalize_whitespace("hello\t\nworld") == "hello world"


def test_normalize_whitespace_already_clean():
    assert normalize_whitespace("hello world") == "hello world"


def test_normalize_whitespace_empty_string():
    assert normalize_whitespace("") == ""


def test_normalize_whitespace_only_whitespace():
    assert normalize_whitespace("   ") == ""


# ---------------------------------------------------------------------------
# Regression: edge cases that relied on the fixed except (ValueError, IndexError)
# ---------------------------------------------------------------------------


def test_mask_email_only_at_sign():
    """'@' → user='' domain='' — short-circuit branch returns '*@', no crash."""
    assert mask_email("@") == "*@"


def test_mask_email_double_at_sign():
    """'@@' has two '@' chars — ValueError path must be caught."""
    assert mask_email("@@") == "***"
