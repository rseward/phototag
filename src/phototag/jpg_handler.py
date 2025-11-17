"""JPG file handler for EXIF operations."""

import os
from datetime import datetime
from pathlib import Path
from PIL import Image
import piexif


class JPGHandler:
    """Handler for JPG file EXIF operations."""

    def __init__(self, filepath: str | Path):
        """Initialize JPG handler with file path.

        Args:
            filepath: Path to the JPG file
        """
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {self.filepath}")
        if self.filepath.suffix.lower() not in [".jpg", ".jpeg"]:
            raise ValueError(f"File is not a JPG: {self.filepath}")

    def set_exif_date(self, date: datetime) -> None:
        """Set EXIF date information in the JPG file.

        Args:
            date: DateTime object to set as EXIF date
        """
        # Load the image
        img = Image.open(self.filepath)

        # Format dates according to EXIF standards
        # EXIF:DateTime format: "YYYY:MM:DD HH:MM:SS"
        datetime_str = date.strftime("%Y:%m:%d %H:%M:%S")

        # Load existing EXIF data or create new
        try:
            exif_dict = piexif.load(img.info.get("exif", b""))
        except Exception:
            # If loading fails, start with empty EXIF dict
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        # Ensure required sections exist
        if "0th" not in exif_dict:
            exif_dict["0th"] = {}
        if "Exif" not in exif_dict:
            exif_dict["Exif"] = {}

        # Set EXIF date tags
        # DateTime in 0th IFD (Image File Directory)
        exif_dict["0th"][piexif.ImageIFD.DateTime] = datetime_str.encode("ascii")

        # DateTimeOriginal and DateTimeDigitized in Exif IFD
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = datetime_str.encode("ascii")
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = datetime_str.encode("ascii")

        # Dump EXIF data to bytes
        exif_bytes = piexif.dump(exif_dict)

        # Save the image with new EXIF data
        img.save(self.filepath, exif=exif_bytes, quality=95, optimize=False)

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
        """Get EXIF date-related fields from the JPG file.

        Returns:
            Dictionary with EXIF date fields (DateTime, DateTimeOriginal, etc.)
        """
        img = Image.open(self.filepath)

        exif_fields = {
            "DateTime": None,
            "DateTimeOriginal": None,
            "DateTimeDigitized": None,
            "CreateDate": None,
        }

        try:
            exif_data = img.info.get("exif")
            if exif_data:
                exif_dict = piexif.load(exif_data)

                # Extract DateTime from 0th IFD
                if "0th" in exif_dict and piexif.ImageIFD.DateTime in exif_dict["0th"]:
                    datetime_bytes = exif_dict["0th"][piexif.ImageIFD.DateTime]
                    exif_fields["DateTime"] = datetime_bytes.decode("ascii")

                # Extract DateTimeOriginal and DateTimeDigitized from Exif IFD
                if "Exif" in exif_dict:
                    if piexif.ExifIFD.DateTimeOriginal in exif_dict["Exif"]:
                        datetime_bytes = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal]
                        exif_fields["DateTimeOriginal"] = datetime_bytes.decode("ascii")

                    if piexif.ExifIFD.DateTimeDigitized in exif_dict["Exif"]:
                        datetime_bytes = exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized]
                        exif_fields["DateTimeDigitized"] = datetime_bytes.decode("ascii")

                # For JPG, CreateDate is typically the same as DateTimeOriginal
                # Set it to DateTimeOriginal if available, otherwise DateTime
                exif_fields["CreateDate"] = (
                    exif_fields["DateTimeOriginal"] or exif_fields["DateTime"]
                )

        except Exception:
            # If there's any error reading EXIF, return None values
            pass

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
