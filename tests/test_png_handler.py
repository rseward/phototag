"""Tests for PNG handler."""

import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path
from PIL import Image
from phototag.png_handler import PNGHandler


@pytest.fixture
def temp_png():
    """Create a temporary PNG file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        # Create a simple test image
        img = Image.new("RGB", (100, 100), color="red")
        img.save(f.name)
        yield f.name
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)


def test_png_handler_init_valid(temp_png):
    """Test PNG handler initialization with valid file."""
    handler = PNGHandler(temp_png)
    assert handler.filepath == Path(temp_png)


def test_png_handler_init_missing_file():
    """Test PNG handler initialization with missing file."""
    with pytest.raises(FileNotFoundError):
        PNGHandler("/nonexistent/file.png")


def test_png_handler_init_non_png():
    """Test PNG handler initialization with non-PNG file."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        try:
            with pytest.raises(ValueError, match="File is not a PNG"):
                PNGHandler(f.name)
        finally:
            os.unlink(f.name)


def test_set_exif_date(temp_png):
    """Test setting EXIF date in PNG file."""
    handler = PNGHandler(temp_png)
    test_date = datetime(2025, 11, 3, 14, 30, 0)

    handler.set_exif_date(test_date)

    # Verify the date was set by reading the file
    img = Image.open(temp_png)
    assert "DateTime" in img.text
    assert img.text["DateTime"] == "2025:11:03 14:30:00"
    assert "DateTimeOriginal" in img.text
    assert "DateTimeDigitized" in img.text


def test_set_file_timestamps(temp_png):
    """Test setting file modification timestamps."""
    handler = PNGHandler(temp_png)
    test_date = datetime(2025, 11, 3, 0, 0, 0)

    handler.set_file_timestamps(test_date)

    # Verify the timestamp was set
    stat_result = Path(temp_png).stat()
    mtime = datetime.fromtimestamp(stat_result.st_mtime)

    # Compare dates (not exact time due to potential precision issues)
    assert mtime.year == test_date.year
    assert mtime.month == test_date.month
    assert mtime.day == test_date.day


def test_get_modification_time(temp_png):
    """Test getting file modification time."""
    handler = PNGHandler(temp_png)

    # Set a known modification time
    test_date = datetime(2021, 5, 1, 10, 30, 0)
    handler.set_file_timestamps(test_date)

    # Get the modification time
    mod_time = handler.get_modification_time()

    assert mod_time.year == 2021
    assert mod_time.month == 5
    assert mod_time.day == 1
