"""Tests for utility functions."""

import pytest
from datetime import datetime
from phototag.utils import parse_date


def test_parse_date_valid():
    """Test parsing valid date strings."""
    result = parse_date("20251103")
    assert result.year == 2025
    assert result.month == 11
    assert result.day == 3
    assert result.hour == 0
    assert result.minute == 0
    assert result.second == 0


def test_parse_date_historic():
    """Test parsing historic dates."""
    result = parse_date("19710501")
    assert result.year == 1971
    assert result.month == 5
    assert result.day == 1


def test_parse_date_invalid_length():
    """Test that invalid length raises ValueError."""
    with pytest.raises(ValueError, match="must be in YYYYMMDD format"):
        parse_date("2025110")

    with pytest.raises(ValueError, match="must be in YYYYMMDD format"):
        parse_date("202511033")


def test_parse_date_invalid_values():
    """Test that invalid date values raise ValueError."""
    with pytest.raises(ValueError, match="Invalid date format"):
        parse_date("20251399")  # Invalid month

    with pytest.raises(ValueError, match="Invalid date format"):
        parse_date("20251132")  # Invalid day


def test_parse_date_invalid_format():
    """Test that non-numeric input raises ValueError."""
    with pytest.raises(ValueError):
        parse_date("abcd1103")
