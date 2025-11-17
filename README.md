# phototag

A Python utility for managing EXIF date information and file timestamps in image files. Supports both PNG and JPG/JPEG formats. Synchronize your image files' EXIF metadata with their filesystem timestamps, or use their existing modification times to set EXIF dates.

## Features

- **Multiple Format Support**: Works with both PNG and JPG/JPEG files
- **Set EXIF Dates**: Write date information into image EXIF metadata fields
- **Sync File Timestamps**: Update file modification times to match EXIF dates
- **Preserve Timestamps**: Use existing file modification times to set EXIF data
- **Synchronize Dates**: Automatically sync all date fields to the oldest date found
- **Batch Processing**: Process multiple files with glob patterns and progress bars
- **Mixed Format Support**: Process PNG and JPG files together in a single command
- **Inspect Metadata**: Display EXIF date fields and file timestamps
- **List Date Information**: Quick columnar overview of date info for multiple files
- **Performance Stats**: See processing speeds for batch operations

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone <repository-url>
cd phototag

# Install with uv
uv sync

# Run the utility
uv run phototag --help
```

### Using pip

```bash
pip install -e .
```

## Usage

### Basic Commands

#### Set an explicit date

Set EXIF date fields and file modification time to a specific date:

```bash
phototag --date="20251103" my-photo.png
phototag --date="20251103" my-photo.jpg
```

This will:
- Set EXIF DateTime to 2025-11-03 00:00:00
- Set file modification time to 2025-11-03 00:00:00

#### Use file modification time

Preserve the file's modification time and write it to EXIF fields:

```bash
phototag --date="mod" my-photo.png
phototag --date="mod" my-photo.jpg
```

This will:
- Read the file's current modification time
- Write it to EXIF metadata (DateTime, DateTimeOriginal, etc.)
- Restore the original modification time after writing

#### Process multiple files

Use glob patterns to process multiple files at once:

```bash
phototag --date="mod" *.png
phototag --date="mod" *.jpg
phototag --date="20201215" photos/*.png photos/*.jpg
```

Multiple files will show a progress bar and performance statistics:
```
Processing files: 100%|██████████| 50/50 [00:00<00:00, 1041.03file/s]
Processed 50 file(s) successfully in 0.048s (0.001s per file)
```

#### Show EXIF and file information

Display EXIF date fields and file timestamps:

```bash
phototag show my-image.png
phototag show my-image.jpg
phototag show photo1.png photo2.jpg  # Multiple files
```

Output:
```
============================================================
File: my-image.png
============================================================

EXIF Date Fields:
----------------------------------------
  DateTime            : 2025:11:03 14:30:00
  DateTimeOriginal    : 2025:11:03 14:30:00
  DateTimeDigitized   : 2025:11:03 14:30:00
  CreateDate          : 2025:11:03

File Timestamps:
----------------------------------------
  Modification Time   : 2025-11-03 14:30:00
```

#### List date information

Display a quick columnar overview of date information for multiple files:

```bash
phototag ls *.png
phototag ls *.jpg
phototag ls *.png *.jpg  # Mix formats
```

Output (sorted by EXIF DateTime, oldest first):
```
Path                    Size  EXIF DateTime        File Modified
------------------------------------------------------------------------
photo2.png              929B  1980:06:15 00:00:00  1980-06-15 00:00:00
photo1.jpg              758B  1985:04:20 00:00:00  1985-04-20 00:00:00
photo3.png           822.7KB  2025:11:03 14:30:00  2025-11-03 14:30:00
```

List in reverse order (oldest last):

```bash
phototag ls -r *.png *.jpg
# or
phototag ls -ltr *.png *.jpg
```

### Examples

#### Organize old family photos

You have scanned photos from May 1, 1971 (works with both PNG and JPG):

```bash
phototag --date="19710501" 1971-mother-and-i.png
phototag --date="19710501" 1971-mother-and-i.jpg
```

#### Batch update vacation photos

Set all vacation photos to their file modification dates:

```bash
phototag --date="mod" vacation-2024/*.png
phototag --date="mod" vacation-2024/*.jpg
phototag --date="mod" vacation-2024/*.png vacation-2024/*.jpg  # Process all at once
```

#### Verify photo metadata

Check what EXIF data a file contains:

```bash
phototag show vacation-2024/beach-sunset.png
phototag show vacation-2024/beach-sunset.jpg
```

#### Quick overview of multiple photos

Get a columnar list of date information for all photos:

```bash
phototag ls vacation-2024/*.png
phototag ls vacation-2024/*.jpg
phototag ls vacation-2024/*  # All supported formats
```

#### Synchronize inconsistent dates

Fix photos with mismatched date fields by using the oldest date:

```bash
phototag sync old-family-photos/*.png
phototag sync old-family-photos/*.jpg
phototag sync old-family-photos/*  # All supported formats
```

This will find the oldest date among all EXIF fields and the file modification time, then synchronize all fields to match.

#### Set specific date for a batch

Tag all photos from a specific event:

```bash
phototag --date="20231225" christmas-2023/*.png christmas-2023/*.jpg
```

#### Process mixed formats

Process both PNG and JPG files in a single command:

```bash
# Tag all images from a trip
phototag --date="20240815" travel/*.png travel/*.jpg

# Show info for mixed formats
phototag show photo1.png photo2.jpg photo3.png

# List all images sorted by date
phototag ls photos/*
```

## Command Reference

### Tag Command (Default)

```bash
phototag --date=<DATE> <FILES...>
```

**Options:**
- `--date=YYYYMMDD`: Set explicit date (e.g., `20251103`)
- `--date=mod`: Use file's current modification time

**Arguments:**
- `<FILES...>`: One or more image files (PNG/JPG/JPEG) or glob patterns

**Behavior:**
- **With explicit date**: Sets EXIF date and file modification time to the specified date
- **With "mod"**: Reads file modification time, writes to EXIF, preserves modification time

### Show Command

```bash
phototag show <FILES...>
```

**Arguments:**
- `<FILES...>`: One or more image files (PNG/JPG/JPEG) to inspect

**Output:**
- EXIF date fields (DateTime, DateTimeOriginal, DateTimeDigitized, CreateDate)
- File modification time

### List Command

```bash
phototag ls [OPTIONS] <FILES...>
```

**Purpose:**
Display date information for multiple image files in a columnar format, similar to the Unix `ls` command. Files are sorted by EXIF DateTime (oldest first) by default. Supports both PNG and JPG/JPEG files.

**Options:**
- `-l`: Long format (default, option ignored for compatibility)
- `-t`: Sort by time (default, option ignored for compatibility)
- `-r`, `--reverse`: Reverse sort order (oldest last)

**Arguments:**
- `<FILES...>`: One or more image files (PNG/JPG/JPEG) or glob patterns

**Output:**
A table with four columns, sorted by EXIF DateTime:
- **Path**: File path
- **Size**: File size in human-readable units (B, KB, MB, GB, TB)
- **EXIF DateTime**: The EXIF DateTime field (or "(not set)" if missing)
- **File Modified**: File modification timestamp

**Sorting:**
- Default: Files sorted by EXIF DateTime, oldest first
- Files without EXIF DateTime appear at the end
- Use `-r` or `--reverse` to sort oldest last (newest first)
- Options `-l` and `-t` are accepted for Unix `ls` compatibility but ignored

**Examples:**
```bash
# List files sorted by date (oldest first)
phototag ls *.png
phototag ls *.jpg

# List mixed formats
phototag ls *.png *.jpg

# List in reverse order (oldest last)
phototag ls -r *.png *.jpg

# Use Unix-style flags (same as -r)
phototag ls -ltr *.png *.jpg

# List specific files
phototag ls photo1.png photo2.jpg photo3.png

# List all image files in directory
phototag ls photos/*
```

**Use Case:**
Get a quick overview of file size and date information across multiple files without the detailed output of the `show` command. Useful for finding oldest or newest photos in a collection. Works seamlessly with both PNG and JPG files.

### Sync Command

```bash
phototag sync <FILES...>
```

**Purpose:**
Synchronizes all date/time fields by finding the oldest date among EXIF metadata and file modification time, then updating all fields to match. Supports both PNG and JPG/JPEG files.

**Arguments:**
- `<FILES...>`: One or more image files (PNG/JPG/JPEG) or glob patterns

**Behavior:**
1. Reads EXIF DateTime (preferred), DateTimeOriginal, CreateDate fields
2. Reads file modification time
3. Finds the oldest date among all available dates
4. Sets all EXIF date fields to the oldest date
5. Sets file modification time to the oldest date

**Example:**
```bash
# Sync a single file
phototag sync my-photo.png
phototag sync my-photo.jpg

# Sync multiple files with progress bar
phototag sync photos/*.png
phototag sync photos/*.jpg

# Sync mixed formats
phototag sync photos/*.png photos/*.jpg
```

**Use Case:**
Useful when photos have inconsistent date information across different fields. The sync command ensures all date fields agree by using the oldest (most trustworthy) date found. Works with both PNG and JPG files.

## Date Format

Dates must be specified in `YYYYMMDD` format:

- ✓ `20251103` - November 3, 2025
- ✓ `19710501` - May 1, 1971
- ✓ `20000101` - January 1, 2000
- ✗ `2025-11-03` - Invalid (contains dashes)
- ✗ `11/03/2025` - Invalid (wrong format)

## EXIF Fields Set

The utility sets the following EXIF fields in PNG metadata:

- **DateTime**: Date and time of image modification
- **DateTimeOriginal**: Date and time when original image was generated
- **DateTimeDigitized**: Date and time when image was digitized
- **CreateDate**: Date when image was created

## Development

### Project Structure

```
phototag/
├── src/phototag/
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── png_handler.py      # PNG EXIF operations
│   ├── jpg_handler.py      # JPG EXIF operations
│   └── utils.py            # Utility functions
├── tests/
│   ├── test_cli.py         # CLI tests
│   ├── test_png_handler.py # PNG handler tests
│   ├── test_jpg_handler.py # JPG handler tests
│   └── test_utils.py       # Utility tests
├── pyproject.toml          # Project configuration
├── Makefile                # Development tasks
└── README.md
```

### Running Tests

```bash
# Run all tests
make test

# Or use pytest directly
uv run pytest tests/ -v
```

### Requirements

- Python >= 3.13
- Dependencies:
  - `pillow` - Image processing (PNG and JPG)
  - `piexif` - EXIF handling for JPG files
  - `click` - Command-line interface
  - `tqdm` - Progress bars

## Technical Details

### How It Works

1. **Reading**: Opens image files using Pillow and reads existing metadata
2. **Writing EXIF**:
   - **PNG files**: Adds EXIF date information as PNG text chunks
   - **JPG files**: Uses piexif to write standard EXIF data to JPG files
3. **Timestamp Management**: Uses `os.utime()` to set file modification times
4. **Preservation**: When using "mod" mode, captures timestamp before writing and restores it after

### File Timestamps

The utility manages file timestamps as follows:

- **Modification Time (mtime)**: Always set to match the EXIF date (or preserved with "mod")
- **Access Time (atime)**: Always set to match the EXIF date (or preserved with "mod")
- **Creation Time**: Platform-dependent behavior:
  - **macOS/BSD**: True birthtime is preserved (cannot be modified)
  - **Windows**: Creation time set via `os.utime()` (may work depending on filesystem)
  - **Linux**: ctime (metadata change time) automatically updated by filesystem when metadata changes

When using `--date="mod"`, the utility:
1. Reads the current modification time
2. Writes EXIF metadata (which updates ctime)
3. Restores the original modification time and access time

### Limitations

- Supports PNG and JPG/JPEG files only
- **PNG files**: EXIF data stored as PNG text chunks (not standard EXIF format)
- **JPG files**: Uses standard EXIF format via piexif library
- True creation time (birthtime) cannot be directly set on most Unix systems
  - On Linux, ctime is metadata change time and updates automatically
  - On macOS/BSD, birthtime is immutable after file creation
  - Windows behavior varies by filesystem
- JPG files are re-saved when updating EXIF data (quality=95 to minimize loss)

## Contributing

Contributions are welcome! Please ensure tests pass before submitting pull requests:

```bash
make test
```

## License

[Add your license here]

## Acknowledgments

Built with:
- [Pillow](https://python-pillow.org/) - Python Imaging Library
- [Click](https://click.palletsprojects.com/) - Command-line interface creation
- [tqdm](https://tqdm.github.io/) - Progress bar library
- [uv](https://github.com/astral-sh/uv) - Python package management
