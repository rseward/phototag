"""Utility functions for date parsing and file operations."""

from datetime import datetime


def parse_date(date_str: str) -> datetime:
    """Parse a date string into a datetime object.

    Args:
        date_str: Date string in format YYYYMMDD

    Returns:
        DateTime object parsed from the string

    Raises:
        ValueError: If date string format is invalid
    """
    if len(date_str) != 8:
        raise ValueError(
            f"Date must be in YYYYMMDD format (8 digits), got: {date_str}"
        )

    try:
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        return datetime(year, month, day, 0, 0, 0)
    except ValueError as e:
        raise ValueError(f"Invalid date format '{date_str}': {e}") from e


def parse_datetime_from_timestamp(timestamp: datetime) -> datetime:
    """Convert a datetime with time information.

    Args:
        timestamp: DateTime object with time information

    Returns:
        DateTime object with full date and time
    """
    return timestamp
