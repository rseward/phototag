"""Tests for JPG handler."""

import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path
from PIL import Image
from phototag.jpg_handler import JPGHandler


@pytest.fixture
def temp_jpg():
    """Create a temporary JPG file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        # Create a simple test image
        img = Image.new("RGB", (100, 100), color="red")
        img.save(f.name, quality=95)
        yield f.name
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)


def test_jpg_handler_init_valid(temp_jpg):
    """Test JPG handler initialization with valid file."""
    handler = JPGHandler(temp_jpg)
    assert handler.filepath == Path(temp_jpg)


def test_jpg_handler_init_valid_jpeg_extension():
    """Test JPG handler initialization with .jpeg extension."""
    with tempfile.NamedTemporaryFile(suffix=".jpeg", delete=False) as f:
        img = Image.new("RGB", (100, 100), color="red")
        img.save(f.name, quality=95)
        try:
            handler = JPGHandler(f.name)
            assert handler.filepath == Path(f.name)
        finally:
            os.unlink(f.name)


def test_jpg_handler_init_missing_file():
    """Test JPG handler initialization with missing file."""
    with pytest.raises(FileNotFoundError):
        JPGHandler("/nonexistent/file.jpg")


def test_jpg_handler_init_non_jpg():
    """Test JPG handler initialization with non-JPG file."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        try:
            with pytest.raises(ValueError, match="File is not a JPG"):
                JPGHandler(f.name)
        finally:
            os.unlink(f.name)


def test_set_exif_date(temp_jpg):
    """Test setting EXIF date in JPG file."""
    handler = JPGHandler(temp_jpg)
    test_date = datetime(2025, 11, 3, 14, 30, 0)

    handler.set_exif_date(test_date)

    # Verify the date was set by reading the file
    exif_dates = handler.get_exif_dates()
    assert exif_dates["DateTime"] == "2025:11:03 14:30:00"
    assert exif_dates["DateTimeOriginal"] == "2025:11:03 14:30:00"
    assert exif_dates["DateTimeDigitized"] == "2025:11:03 14:30:00"


def test_set_file_timestamps(temp_jpg):
    """Test setting file modification timestamps."""
    handler = JPGHandler(temp_jpg)
    test_date = datetime(2025, 11, 3, 0, 0, 0)

    handler.set_file_timestamps(test_date)

    # Verify the timestamp was set
    stat_result = Path(temp_jpg).stat()
    mtime = datetime.fromtimestamp(stat_result.st_mtime)

    # Compare dates (not exact time due to potential precision issues)
    assert mtime.year == test_date.year
    assert mtime.month == test_date.month
    assert mtime.day == test_date.day


def test_get_modification_time(temp_jpg):
    """Test getting file modification time."""
    handler = JPGHandler(temp_jpg)

    # Set a known modification time
    test_date = datetime(2021, 5, 1, 10, 30, 0)
    handler.set_file_timestamps(test_date)

    # Get the modification time
    mod_time = handler.get_modification_time()

    assert mod_time.year == 2021
    assert mod_time.month == 5
    assert mod_time.day == 1


def test_get_exif_dates_no_exif(temp_jpg):
    """Test getting EXIF dates from JPG with no EXIF data."""
    handler = JPGHandler(temp_jpg)
    exif_dates = handler.get_exif_dates()

    # Should return None for all fields when no EXIF data
    assert exif_dates["DateTime"] is None
    assert exif_dates["DateTimeOriginal"] is None
    assert exif_dates["DateTimeDigitized"] is None


def test_parse_exif_datetime_valid():
    """Test parsing valid EXIF datetime string."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img = Image.new("RGB", (100, 100), color="red")
        img.save(f.name, quality=95)
        try:
            handler = JPGHandler(f.name)
            dt = handler.parse_exif_datetime("2025:11:03 14:30:00")
            assert dt == datetime(2025, 11, 3, 14, 30, 0)
        finally:
            os.unlink(f.name)


def test_parse_exif_datetime_date_only():
    """Test parsing EXIF date-only string."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img = Image.new("RGB", (100, 100), color="red")
        img.save(f.name, quality=95)
        try:
            handler = JPGHandler(f.name)
            dt = handler.parse_exif_datetime("2025:11:03")
            assert dt == datetime(2025, 11, 3, 0, 0, 0)
        finally:
            os.unlink(f.name)


def test_parse_exif_datetime_invalid():
    """Test parsing invalid EXIF datetime string."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img = Image.new("RGB", (100, 100), color="red")
        img.save(f.name, quality=95)
        try:
            handler = JPGHandler(f.name)
            dt = handler.parse_exif_datetime("invalid")
            assert dt is None
        finally:
            os.unlink(f.name)


def test_get_oldest_date_with_exif(temp_jpg):
    """Test getting oldest date when EXIF data exists."""
    handler = JPGHandler(temp_jpg)

    # Set EXIF date to a specific date
    exif_date = datetime(2020, 1, 1, 12, 0, 0)
    handler.set_exif_date(exif_date)

    # Set file modification time to a newer date
    file_date = datetime(2021, 1, 1, 12, 0, 0)
    handler.set_file_timestamps(file_date)

    # The oldest date should be the EXIF date
    oldest = handler.get_oldest_date()
    assert oldest.year == 2020
    assert oldest.month == 1
    assert oldest.day == 1


def test_get_oldest_date_no_exif(temp_jpg):
    """Test getting oldest date when no EXIF data exists."""
    handler = JPGHandler(temp_jpg)

    # Set file modification time
    file_date = datetime(2021, 5, 1, 10, 30, 0)
    handler.set_file_timestamps(file_date)

    # Should return the file modification time
    oldest = handler.get_oldest_date()
    assert oldest.year == 2021
    assert oldest.month == 5
    assert oldest.day == 1


def test_round_trip_exif_dates(temp_jpg):
    """Test that we can set and retrieve EXIF dates correctly."""
    handler = JPGHandler(temp_jpg)
    test_date = datetime(1971, 5, 1, 14, 30, 0)

    # Set EXIF date
    handler.set_exif_date(test_date)

    # Retrieve and verify
    exif_dates = handler.get_exif_dates()
    assert exif_dates["DateTime"] == "1971:05:01 14:30:00"
    assert exif_dates["DateTimeOriginal"] == "1971:05:01 14:30:00"
    assert exif_dates["DateTimeDigitized"] == "1971:05:01 14:30:00"

    # Parse it back to datetime
    parsed = handler.parse_exif_datetime(exif_dates["DateTime"])
    assert parsed == test_date
