"""Tests for CLI functionality."""

import tempfile
import os
from pathlib import Path
from datetime import datetime
from click.testing import CliRunner
from PIL import Image
from phototag.cli import main, tag_command, show_command


def test_cli_single_file():
    """Test CLI with a single file."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test PNG
        test_file = Path(tmpdir) / "test.png"
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(test_file)

        # Run the CLI using tag subcommand
        result = runner.invoke(main, ["tag", "--date=20251103", str(test_file)])

        assert result.exit_code == 0
        assert "Successfully processed" in result.output
        assert "Processed 1 file(s) successfully" in result.output


def test_cli_multiple_files():
    """Test CLI with multiple files (should show progress bar)."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple test PNGs
        test_files = []
        for i in range(3):
            test_file = Path(tmpdir) / f"test{i}.png"
            img = Image.new("RGB", (100, 100), color="red")
            img.save(test_file)
            test_files.append(str(test_file))

        # Run the CLI
        result = runner.invoke(main, ["tag", "--date=20251103"] + test_files)

        assert result.exit_code == 0
        assert "Processed 3 file(s) successfully" in result.output


def test_cli_with_mod_date():
    """Test CLI with 'mod' date option."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test PNG
        test_file = Path(tmpdir) / "test.png"
        img = Image.new("RGB", (100, 100), color="green")
        img.save(test_file)

        # Run the CLI with 'mod' option
        result = runner.invoke(main, ["tag", "--date=mod", str(test_file)])

        assert result.exit_code == 0
        assert "Using modification time" in result.output or "Processed 1 file(s) successfully" in result.output


def test_cli_missing_file():
    """Test CLI with non-existent file."""
    runner = CliRunner()

    result = runner.invoke(main, ["tag", "--date=20251103", "/nonexistent/file.png"])

    assert result.exit_code == 1
    assert "Error" in result.output


def test_cli_invalid_date():
    """Test CLI with invalid date format."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test PNG
        test_file = Path(tmpdir) / "test.png"
        img = Image.new("RGB", (100, 100), color="yellow")
        img.save(test_file)

        # Run with invalid date
        result = runner.invoke(main, ["tag", "--date=invalid", str(test_file)])

        assert result.exit_code == 1
        assert "Error" in result.output


def test_cli_help():
    """Test CLI help output."""
    runner = CliRunner()

    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "photo tagging utility" in result.output
    assert "--date" in result.output


def test_cli_mod_preserves_modification_time():
    """Test that 'mod' mode preserves the original file modification time."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test PNG
        test_file = Path(tmpdir) / "test.png"
        img = Image.new("RGB", (100, 100), color="cyan")
        img.save(test_file)

        # Set a specific modification time (June 15, 1980)
        test_date = datetime(1980, 6, 15, 10, 30, 45)
        timestamp = test_date.timestamp()
        os.utime(test_file, (timestamp, timestamp))

        # Get the modification time before processing
        mtime_before = test_file.stat().st_mtime

        # Run the CLI with 'mod' option
        result = runner.invoke(main, ["tag", "--date=mod", str(test_file)])

        assert result.exit_code == 0

        # Get the modification time after processing
        mtime_after = test_file.stat().st_mtime

        # The modification time should be preserved (within 1 second tolerance)
        assert abs(mtime_after - mtime_before) < 1.0

        # Verify EXIF data was set
        img_after = Image.open(test_file)
        assert "DateTime" in img_after.text
        # EXIF should have the original modification time
        assert img_after.text["DateTime"].startswith("1980:06:15")


def test_cli_explicit_date_sets_modification_time():
    """Test that explicit date sets the file modification time to match EXIF."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test PNG
        test_file = Path(tmpdir) / "test.png"
        img = Image.new("RGB", (100, 100), color="magenta")
        img.save(test_file)

        # Run the CLI with explicit date
        result = runner.invoke(main, ["tag", "--date=19900815", str(test_file)])

        assert result.exit_code == 0

        # Get the modification time after processing
        mtime_after = datetime.fromtimestamp(test_file.stat().st_mtime)

        # The modification time should match the explicit date (1990-08-15)
        assert mtime_after.year == 1990
        assert mtime_after.month == 8
        assert mtime_after.day == 15

        # Verify EXIF data was set to the same date
        img_after = Image.open(test_file)
        assert "DateTime" in img_after.text
        assert img_after.text["DateTime"] == "1990:08:15 00:00:00"


def test_cli_show_command():
    """Test the show command displays EXIF and file info."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create and tag a test PNG
        test_file = Path(tmpdir) / "test.png"
        img = Image.new("RGB", (100, 100), color="purple")
        img.save(test_file)

        # First tag it with a date
        tag_result = runner.invoke(main, ["tag", "--date=19850420", str(test_file)])
        assert tag_result.exit_code == 0

        # Now show the info
        show_result = runner.invoke(main, ["show", str(test_file)])

        assert show_result.exit_code == 0
        assert "EXIF Date Fields" in show_result.output
        assert "File Timestamps" in show_result.output
        assert "DateTime" in show_result.output
        assert "1985:04:20" in show_result.output


def test_cli_sync_command():
    """Test the sync command synchronizes dates to oldest."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test PNG with mismatched dates
        from PIL.PngImagePlugin import PngInfo

        test_file = Path(tmpdir) / "test.png"
        img = Image.new("RGB", (100, 100), color="orange")

        # Add EXIF with different dates
        metadata = PngInfo()
        metadata.add_text("DateTime", "1980:06:15 10:30:45")  # Oldest
        metadata.add_text("DateTimeOriginal", "1990:01:01 00:00:00")  # Newer

        img.save(test_file, pnginfo=metadata)

        # Set file modification time to even newer date
        newer_date = datetime(2000, 12, 25, 15, 45, 30)
        os.utime(test_file, (newer_date.timestamp(), newer_date.timestamp()))

        # Run sync command
        result = runner.invoke(main, ["sync", str(test_file)])

        assert result.exit_code == 0
        assert "Successfully synced" in result.output
        assert "1980-06-15 10:30:45" in result.output

        # Verify all dates are now synchronized
        img_after = Image.open(test_file)
        assert img_after.text["DateTime"] == "1980:06:15 10:30:45"
        assert img_after.text["DateTimeOriginal"] == "1980:06:15 10:30:45"
        assert img_after.text["DateTimeDigitized"] == "1980:06:15 10:30:45"

        # Verify file modification time was updated
        mtime_after = datetime.fromtimestamp(test_file.stat().st_mtime)
        assert mtime_after.year == 1980
        assert mtime_after.month == 6
        assert mtime_after.day == 15


def test_cli_sync_multiple_files():
    """Test sync command with multiple files."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple test PNGs
        test_files = []
        for i in range(3):
            test_file = Path(tmpdir) / f"test{i}.png"
            img = Image.new("RGB", (100, 100), color="blue")
            img.save(test_file)
            test_files.append(str(test_file))

        # Run sync on all files
        result = runner.invoke(main, ["sync"] + test_files)

        assert result.exit_code == 0
        assert "Synced 3 file(s) successfully" in result.output
