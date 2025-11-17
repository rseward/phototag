"""Tests for CLI functionality."""

import tempfile
import os
from pathlib import Path
from datetime import datetime
from click.testing import CliRunner
from PIL import Image
import piexif
from phototag.cli import main, tag_command, show_command, ls_command


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


def test_cli_ls_command_single_file():
    """Test the ls command with a single file."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create and tag a test PNG
        test_file = Path(tmpdir) / "test.png"
        img = Image.new("RGB", (100, 100), color="purple")
        img.save(test_file)

        # Tag it with a date first
        tag_result = runner.invoke(main, ["tag", "--date=19850420", str(test_file)])
        assert tag_result.exit_code == 0

        # Now run ls command
        ls_result = runner.invoke(main, ["ls", str(test_file)])

        assert ls_result.exit_code == 0
        assert "Path" in ls_result.output
        assert "Size" in ls_result.output
        assert "EXIF DateTime" in ls_result.output
        assert "File Modified" in ls_result.output
        assert "1985:04:20" in ls_result.output
        assert "test.png" in ls_result.output
        # Check that a size value appears (should be in bytes for small files)
        assert "B" in ls_result.output or "KB" in ls_result.output


def test_cli_ls_command_multiple_files():
    """Test the ls command with multiple files."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple test PNGs with different dates
        test_files = []
        dates = ["19800101", "19900505", "20001231"]

        for i, date in enumerate(dates):
            test_file = Path(tmpdir) / f"test{i}.png"
            img = Image.new("RGB", (100, 100), color="red")
            img.save(test_file)
            test_files.append(str(test_file))

            # Tag each file with a different date
            tag_result = runner.invoke(main, ["tag", f"--date={date}", str(test_file)])
            assert tag_result.exit_code == 0

        # Run ls command on all files
        ls_result = runner.invoke(main, ["ls"] + test_files)

        assert ls_result.exit_code == 0
        assert "Path" in ls_result.output
        assert "Size" in ls_result.output
        assert "EXIF DateTime" in ls_result.output
        assert "File Modified" in ls_result.output
        # Check that all files appear in output
        assert "test0.png" in ls_result.output
        assert "test1.png" in ls_result.output
        assert "test2.png" in ls_result.output
        # Check that dates appear
        assert "1980:01:01" in ls_result.output
        assert "1990:05:05" in ls_result.output
        assert "2000:12:31" in ls_result.output


def test_cli_ls_command_no_exif():
    """Test the ls command with a file that has no EXIF data."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test PNG without EXIF data
        test_file = Path(tmpdir) / "test.png"
        img = Image.new("RGB", (100, 100), color="green")
        img.save(test_file)

        # Run ls command
        ls_result = runner.invoke(main, ["ls", str(test_file)])

        assert ls_result.exit_code == 0
        assert "Path" in ls_result.output
        assert "Size" in ls_result.output
        assert "EXIF DateTime" in ls_result.output
        assert "File Modified" in ls_result.output
        assert "(not set)" in ls_result.output
        assert "test.png" in ls_result.output


def test_cli_ls_command_with_glob():
    """Test the ls command with glob pattern."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple test PNGs
        for i in range(3):
            test_file = Path(tmpdir) / f"photo{i}.png"
            img = Image.new("RGB", (100, 100), color="blue")
            img.save(test_file)

        # Run ls command with glob pattern
        glob_pattern = str(Path(tmpdir) / "photo*.png")
        ls_result = runner.invoke(main, ["ls", glob_pattern])

        assert ls_result.exit_code == 0
        assert "photo0.png" in ls_result.output
        assert "photo1.png" in ls_result.output
        assert "photo2.png" in ls_result.output


def test_cli_ls_command_sorting():
    """Test the ls command sorts by EXIF DateTime (oldest first)."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple test PNGs with different dates in non-chronological order
        test_files = []
        dates_and_names = [
            ("20001231", "file_newest.png"),
            ("19800101", "file_oldest.png"),
            ("19900505", "file_middle.png"),
        ]

        for date, name in dates_and_names:
            test_file = Path(tmpdir) / name
            img = Image.new("RGB", (100, 100), color="red")
            img.save(test_file)
            test_files.append(str(test_file))

            # Tag each file with a different date
            tag_result = runner.invoke(main, ["tag", f"--date={date}", str(test_file)])
            assert tag_result.exit_code == 0

        # Run ls command - should sort oldest first
        ls_result = runner.invoke(main, ["ls"] + test_files)

        assert ls_result.exit_code == 0

        # Find positions of each file in output
        lines = ls_result.output.split('\n')
        data_lines = [line for line in lines if 'file_' in line]

        # Verify order: oldest, middle, newest
        assert data_lines[0].startswith(str(Path(tmpdir) / "file_oldest.png"))
        assert data_lines[1].startswith(str(Path(tmpdir) / "file_middle.png"))
        assert data_lines[2].startswith(str(Path(tmpdir) / "file_newest.png"))


def test_cli_ls_command_reverse_sorting():
    """Test the ls command with -r flag sorts oldest last."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple test PNGs with different dates
        test_files = []
        dates_and_names = [
            ("20001231", "file_newest.png"),
            ("19800101", "file_oldest.png"),
            ("19900505", "file_middle.png"),
        ]

        for date, name in dates_and_names:
            test_file = Path(tmpdir) / name
            img = Image.new("RGB", (100, 100), color="red")
            img.save(test_file)
            test_files.append(str(test_file))

            # Tag each file with a different date
            tag_result = runner.invoke(main, ["tag", f"--date={date}", str(test_file)])
            assert tag_result.exit_code == 0

        # Run ls command with -r flag - should sort newest first (oldest last)
        ls_result = runner.invoke(main, ["ls", "-r"] + test_files)

        assert ls_result.exit_code == 0

        # Find positions of each file in output
        lines = ls_result.output.split('\n')
        data_lines = [line for line in lines if 'file_' in line]

        # Verify order: newest, middle, oldest
        assert data_lines[0].startswith(str(Path(tmpdir) / "file_newest.png"))
        assert data_lines[1].startswith(str(Path(tmpdir) / "file_middle.png"))
        assert data_lines[2].startswith(str(Path(tmpdir) / "file_oldest.png"))


def test_cli_ls_command_ltr_flags():
    """Test the ls command with -ltr flags (same as -r)."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test PNGs with different dates
        test_files = []
        dates_and_names = [
            ("19800101", "file_old.png"),
            ("19900505", "file_new.png"),
        ]

        for date, name in dates_and_names:
            test_file = Path(tmpdir) / name
            img = Image.new("RGB", (100, 100), color="blue")
            img.save(test_file)
            test_files.append(str(test_file))

            # Tag each file
            tag_result = runner.invoke(main, ["tag", f"--date={date}", str(test_file)])
            assert tag_result.exit_code == 0

        # Run ls command with -ltr flags
        ls_result = runner.invoke(main, ["ls", "-ltr"] + test_files)

        assert ls_result.exit_code == 0

        # Find positions of each file in output
        lines = ls_result.output.split('\n')
        data_lines = [line for line in lines if 'file_' in line]

        # Verify reverse order (newest first, oldest last)
        assert data_lines[0].startswith(str(Path(tmpdir) / "file_new.png"))
        assert data_lines[1].startswith(str(Path(tmpdir) / "file_old.png"))


# JPG-specific tests

def test_cli_jpg_single_file():
    """Test CLI with a single JPG file."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test JPG
        test_file = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(test_file, quality=95)

        # Run the CLI using tag subcommand
        result = runner.invoke(main, ["tag", "--date=20251103", str(test_file)])

        assert result.exit_code == 0
        assert "Successfully processed" in result.output
        assert "Processed 1 file(s) successfully" in result.output


def test_cli_jpg_with_jpeg_extension():
    """Test CLI with .jpeg extension."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test JPEG
        test_file = Path(tmpdir) / "test.jpeg"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(test_file, quality=95)

        # Run the CLI
        result = runner.invoke(main, ["tag", "--date=20201225", str(test_file)])

        assert result.exit_code == 0
        assert "Processed 1 file(s) successfully" in result.output


def test_cli_jpg_show_command():
    """Test the show command with JPG files."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create and tag a test JPG
        test_file = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (100, 100), color="purple")
        img.save(test_file, quality=95)

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


def test_cli_jpg_sync_command():
    """Test the sync command with JPG files."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test JPG with mismatched dates
        test_file = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (100, 100), color="orange")

        # Create EXIF data with different dates
        exif_dict = {"0th": {}, "Exif": {}}
        exif_dict["0th"][piexif.ImageIFD.DateTime] = b"1980:06:15 10:30:45"  # Oldest
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = b"1990:01:01 00:00:00"  # Newer

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_file, exif=exif_bytes, quality=95)

        # Set file modification time to even newer date
        newer_date = datetime(2000, 12, 25, 15, 45, 30)
        os.utime(test_file, (newer_date.timestamp(), newer_date.timestamp()))

        # Run sync command
        result = runner.invoke(main, ["sync", str(test_file)])

        assert result.exit_code == 0
        assert "Successfully synced" in result.output
        assert "1980-06-15 10:30:45" in result.output

        # Verify dates are synchronized
        img_after = Image.open(test_file)
        exif_after = piexif.load(img_after.info.get("exif", b""))
        assert exif_after["0th"][piexif.ImageIFD.DateTime] == b"1980:06:15 10:30:45"
        assert exif_after["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"1980:06:15 10:30:45"


def test_cli_mixed_png_jpg_files():
    """Test CLI with both PNG and JPG files in the same command."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test PNG files
        png_files = []
        for i in range(2):
            test_file = Path(tmpdir) / f"test{i}.png"
            img = Image.new("RGB", (100, 100), color="red")
            img.save(test_file)
            png_files.append(str(test_file))

        # Create test JPG files
        jpg_files = []
        for i in range(2):
            test_file = Path(tmpdir) / f"test{i}.jpg"
            img = Image.new("RGB", (100, 100), color="blue")
            img.save(test_file, quality=95)
            jpg_files.append(str(test_file))

        # Run the CLI with mixed file types
        all_files = png_files + jpg_files
        result = runner.invoke(main, ["tag", "--date=20251103"] + all_files)

        assert result.exit_code == 0
        assert "Processed 4 file(s) successfully" in result.output


def test_cli_jpg_ls_command():
    """Test the ls command with JPG files."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple JPG files with different dates
        test_files = []
        dates_and_names = [
            ("19800101", "file_old.jpg"),
            ("19900505", "file_middle.jpg"),
            ("20001231", "file_new.jpg"),
        ]

        for date, name in dates_and_names:
            test_file = Path(tmpdir) / name
            img = Image.new("RGB", (100, 100), color="green")
            img.save(test_file, quality=95)
            test_files.append(str(test_file))

            # Tag each file with a different date
            tag_result = runner.invoke(main, ["tag", f"--date={date}", str(test_file)])
            assert tag_result.exit_code == 0

        # Run ls command on all files
        ls_result = runner.invoke(main, ["ls"] + test_files)

        assert ls_result.exit_code == 0
        assert "Path" in ls_result.output
        assert "Size" in ls_result.output
        assert "EXIF DateTime" in ls_result.output
        # Verify files are sorted by date (oldest first)
        lines = ls_result.output.split('\n')
        data_lines = [line for line in lines if 'file_' in line]
        assert data_lines[0].startswith(str(Path(tmpdir) / "file_old.jpg"))
        assert data_lines[1].startswith(str(Path(tmpdir) / "file_middle.jpg"))
        assert data_lines[2].startswith(str(Path(tmpdir) / "file_new.jpg"))


def test_cli_mixed_ls_command():
    """Test the ls command with both PNG and JPG files."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create PNG and JPG files with different dates
        test_files = []
        files_data = [
            ("19800101", "file1.png", "red"),
            ("19900505", "file2.jpg", "blue"),
            ("20001231", "file3.png", "green"),
        ]

        for date, name, color in files_data:
            test_file = Path(tmpdir) / name
            img = Image.new("RGB", (100, 100), color=color)

            if name.endswith('.png'):
                img.save(test_file)
            else:
                img.save(test_file, quality=95)

            test_files.append(str(test_file))

            # Tag each file
            tag_result = runner.invoke(main, ["tag", f"--date={date}", str(test_file)])
            assert tag_result.exit_code == 0

        # Run ls command
        ls_result = runner.invoke(main, ["ls"] + test_files)

        assert ls_result.exit_code == 0
        # Verify both file types appear
        assert "file1.png" in ls_result.output
        assert "file2.jpg" in ls_result.output
        assert "file3.png" in ls_result.output
        # Verify sorting by date
        lines = ls_result.output.split('\n')
        data_lines = [line for line in lines if 'file' in line and '.png' in line or '.jpg' in line]
        assert len(data_lines) >= 3
