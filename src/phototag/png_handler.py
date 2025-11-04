"""PNG file handler for EXIF operations."""

import os
from datetime import datetime
from pathlib import Path
from PIL import Image
from PIL.PngImagePlugin import PngInfo


class PNGHandler:
    """Handler for PNG file EXIF operations."""

    def __init__(self, filepath: str | Path):
        """Initialize PNG handler with file path.

        Args:
            filepath: Path to the PNG file
        """
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {self.filepath}")
        if self.filepath.suffix.lower() != ".png":
            raise ValueError(f"File is not a PNG: {self.filepath}")

    def set_exif_date(self, date: datetime) -> None:
        """Set EXIF date information in the PNG file.

        Args:
            date: DateTime object to set as EXIF date
        """
        # Load the image
        img = Image.open(self.filepath)

        # Create PNG metadata
        metadata = PngInfo()

        # Copy existing metadata
        if hasattr(img, "text") and img.text:
            for key, value in img.text.items():
                metadata.add_text(key, value)

        # Format dates according to EXIF standards
        # EXIF:DateTime format: "YYYY:MM:DD HH:MM:SS"
        datetime_str = date.strftime("%Y:%m:%d %H:%M:%S")
        date_str = date.strftime("%Y:%m:%d")

        # Add EXIF date tags
        # Using standard EXIF tag names as text chunks in PNG
        metadata.add_text("DateTime", datetime_str)
        metadata.add_text("DateTimeOriginal", datetime_str)
        metadata.add_text("DateTimeDigitized", datetime_str)
        metadata.add_text("CreateDate", date_str)

        # Save the image with new metadata
        img.save(self.filepath, pnginfo=metadata)

    def set_file_timestamps(self, date: datetime) -> None:
        """Set file modification and access times.

        Sets both atime (access time) and mtime (modification time) to the specified date.

        Note: On Unix systems, the creation time (birthtime) cannot be directly modified.
        The ctime (metadata change time) will be automatically updated by the filesystem
        when metadata is changed. On some systems with birthtime support, this remains
        the original file creation time.

        Args:
            date: DateTime object to set as file timestamp
        """
        timestamp = date.timestamp()
        # Set both access time and modification time
        os.utime(self.filepath, (timestamp, timestamp))

    def get_modification_time(self) -> datetime:
        """Get the file's modification time.

        Returns:
            DateTime object representing the file's modification time
        """
        mtime = self.filepath.stat().st_mtime
        return datetime.fromtimestamp(mtime)

    def get_creation_time(self) -> datetime:
        """Get the file's creation time (or ctime on Unix).

        Returns:
            DateTime object representing the file's creation/ctime

        Note: Returns st_birthtime if available (macOS, some BSD systems, some Linux
        filesystems), otherwise returns st_ctime (metadata change time on Unix).
        """
        stat_result = self.filepath.stat()

        # Try to get birthtime (creation time) if available
        # This works on macOS, some BSD systems, and some Linux filesystems
        if hasattr(stat_result, "st_birthtime"):
            return datetime.fromtimestamp(stat_result.st_birthtime)

        # Fall back to ctime (metadata change time on Unix, creation time on Windows)
        return datetime.fromtimestamp(stat_result.st_ctime)

    def get_exif_dates(self) -> dict[str, str | None]:
        """Get EXIF date-related fields from the PNG file.

        Returns:
            Dictionary with EXIF date fields (DateTime, DateTimeOriginal, etc.)
        """
        img = Image.open(self.filepath)

        exif_fields = {}
        if hasattr(img, "text") and img.text:
            # Extract all date-related EXIF fields
            date_keys = [
                "DateTime",
                "DateTimeOriginal",
                "DateTimeDigitized",
                "CreateDate",
            ]
            for key in date_keys:
                exif_fields[key] = img.text.get(key)
        else:
            # No EXIF data found
            exif_fields = {
                key: None
                for key in [
                    "DateTime",
                    "DateTimeOriginal",
                    "DateTimeDigitized",
                    "CreateDate",
                ]
            }

        return exif_fields

    def parse_exif_datetime(self, exif_datetime_str: str) -> datetime | None:
        """Parse EXIF DateTime string to datetime object.

        Args:
            exif_datetime_str: EXIF DateTime string in format "YYYY:MM:DD HH:MM:SS"

        Returns:
            DateTime object or None if parsing fails
        """
        if not exif_datetime_str:
            return None

        try:
            # EXIF DateTime format: "YYYY:MM:DD HH:MM:SS"
            return datetime.strptime(exif_datetime_str, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            # Try date-only format: "YYYY:MM:DD"
            try:
                return datetime.strptime(exif_datetime_str, "%Y:%m:%d")
            except ValueError:
                return None

    def get_oldest_date(self) -> datetime:
        """Find the oldest date among EXIF dates and file modification time.

        Checks DateTime (preferred), then CreateDate from EXIF, and file modification time.
        Returns the oldest date found.

        Returns:
            DateTime object representing the oldest date found

        Raises:
            ValueError: If no valid dates are found
        """
        dates = []

        # Get EXIF dates
        exif_dates = self.get_exif_dates()

        # Try DateTime first (preferred)
        if exif_dates.get("DateTime"):
            dt = self.parse_exif_datetime(exif_dates["DateTime"])
            if dt:
                dates.append(dt)

        # Try DateTimeOriginal
        if exif_dates.get("DateTimeOriginal"):
            dt = self.parse_exif_datetime(exif_dates["DateTimeOriginal"])
            if dt:
                dates.append(dt)

        # Try CreateDate (date-only field)
        if exif_dates.get("CreateDate"):
            dt = self.parse_exif_datetime(exif_dates["CreateDate"])
            if dt:
                dates.append(dt)

        # Get file modification time
        dates.append(self.get_modification_time())

        if not dates:
            raise ValueError(f"No valid dates found in {self.filepath}")

        # Return the oldest date
        return min(dates)
