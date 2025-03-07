"""Unit tests for the converters module."""

from tmt_web.converters import _convert_field_value


def test_convert_field_value_contact_string():
    """Test converting contact from string to list."""
    result = _convert_field_value("contact", "John Doe <john@example.com>")
    assert result == ["John Doe <john@example.com>"]


def test_convert_field_value_contact_list():
    """Test contact already in list form."""
    contacts = ["John Doe <john@example.com>", "Jane Doe <jane@example.com>"]
    result = _convert_field_value("contact", contacts)
    assert result == contacts


def test_convert_field_value_tier_int():
    """Test converting tier from int to string."""
    result = _convert_field_value("tier", 1)
    assert result == "1"


def test_convert_field_value_tier_none():
    """Test converting tier when None."""
    result = _convert_field_value("tier", None)
    assert result is None


def test_convert_field_value_execute_dict():
    """Test converting execute from dict to list."""
    result = _convert_field_value("execute", {"how": "tmt"})
    assert result == [{"how": "tmt"}]


def test_convert_field_value_execute_list():
    """Test execute already in list form."""
    execute = [{"how": "tmt"}, {"how": "shell"}]
    result = _convert_field_value("execute", execute)
    assert result == execute


def test_convert_field_value_discover_list():
    """Test converting discover from list to dict."""
    discover = [{"how": "fmf", "url": "example.com"}]
    result = _convert_field_value("discover", discover)
    assert result == {"how": "fmf", "url": "example.com"}


def test_convert_field_value_discover_dict():
    """Test discover already in dict form."""
    discover = {"how": "fmf", "url": "example.com"}
    result = _convert_field_value("discover", discover)
    assert result == discover


def test_convert_field_value_other_field():
    """Test field that doesn't need conversion."""
    value = "test value"
    result = _convert_field_value("summary", value)
    assert result == value


def test_convert_fmf_id_none():
    """Test converting fmf_id when it doesn't exist."""
    from unittest.mock import MagicMock

    from tmt_web.converters import _convert_fmf_id

    # Create a mock object without fmf_id attribute
    mock_obj = MagicMock()
    # Ensure fmf_id doesn't exist
    if hasattr(mock_obj, "fmf_id"):
        delattr(mock_obj, "fmf_id")

    result = _convert_fmf_id(mock_obj)
    assert result is None
