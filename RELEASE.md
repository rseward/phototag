# Purpose

Document the project releases

# 0.2.0

Major feature release adding full JPG/JPEG support to phototag. The utility now supports both PNG and JPG/JPEG files, with the ability to process mixed file types in a single command.

## New Features

- **JPG/JPEG Support** - Full support for JPG and JPEG image files with proper EXIF handling using the piexif library
- **Mixed Format Processing** - Process both PNG and JPG files together in a single command (e.g., `phototag tag --date=mod *.png *.jpg`)
- **JPG Handler Module** - New `jpg_handler.py` module implementing all PNG features for JPG files
- **Automatic Format Detection** - CLI automatically detects file type and uses appropriate handler

## Updates

- **CLI Commands** - All commands (tag, show, ls, sync) now work with both PNG and JPG files
- **Documentation** - Updated README.md with comprehensive examples for both formats
- **Test Coverage** - Added 21 new tests for JPG functionality (50 total tests, all passing)
- **Dependencies** - Added piexif>=1.1.3 for JPG EXIF handling

## Technical Details

- PNG files: EXIF stored as PNG text chunks (unchanged from 0.1.0)
- JPG files: Standard EXIF format using piexif library
- JPG quality set to 95 to minimize quality loss when updating EXIF data
- Supports .jpg and .jpeg file extensions

# 0.1.0

Initial release of phototag - a Python utility for managing EXIF date information in PNG files.

## Features

- **tag command** - Set EXIF date fields and file timestamps using explicit dates (YYYYMMDD) or file modification time (`--date=mod`)
- **show command** - Display detailed EXIF date fields (DateTime, DateTimeOriginal, DateTimeDigitized, CreateDate) and file modification time
- **ls command** - List file information in a columnar format showing path, file size (human-readable units), EXIF DateTime, and file modification time
- **sync command** - Synchronize all date/time fields by finding the oldest date among EXIF metadata and file modification time, then updating all fields to match
- **Batch processing** - Process multiple files using glob patterns with progress bars and performance statistics
- **Timestamp preservation** - Preserve original file modification times when using `--date=mod` mode
