# Purpose

Document the project releases

# 0.1.0

Initial release of phototag - a Python utility for managing EXIF date information in PNG files.

## Features

- **tag command** - Set EXIF date fields and file timestamps using explicit dates (YYYYMMDD) or file modification time (`--date=mod`)
- **show command** - Display detailed EXIF date fields (DateTime, DateTimeOriginal, DateTimeDigitized, CreateDate) and file modification time
- **ls command** - List file information in a columnar format showing path, file size (human-readable units), EXIF DateTime, and file modification time
- **sync command** - Synchronize all date/time fields by finding the oldest date among EXIF metadata and file modification time, then updating all fields to match
- **Batch processing** - Process multiple files using glob patterns with progress bars and performance statistics
- **Timestamp preservation** - Preserve original file modification times when using `--date=mod` mode
