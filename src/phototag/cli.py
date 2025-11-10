"""Command-line interface for phototag utility."""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import click
from tqdm import tqdm

from .png_handler import PNGHandler
from .utils import parse_date


def process_file(filepath: Path, date_str: str, quiet: bool = False) -> Tuple[bool, str]:
    """Process a single PNG file.

    Args:
        filepath: Path to the PNG file
        date_str: Date string (YYYYMMDD format or "mod")
        quiet: If True, suppress per-file messages

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        handler = PNGHandler(filepath)

        # Determine the date to use
        if date_str.lower() == "mod":
            # Use the file's modification time and preserve it
            date = handler.get_modification_time()
            msg = f"Using modification time for {filepath}: {date.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            # Parse the provided date string
            date = parse_date(date_str)
            msg = f"Setting date for {filepath}: {date.strftime('%Y-%m-%d')}"

        if not quiet:
            click.echo(msg)

        # Set EXIF date
        handler.set_exif_date(date)

        # Always set file timestamps to match the date being used
        # For "mod" mode, this restores the original modification time
        # For explicit dates, this sets the file time to match the EXIF date
        handler.set_file_timestamps(date)

        success_msg = f"✓ Successfully processed {filepath}"
        if not quiet:
            click.echo(success_msg)
        return True, success_msg

    except FileNotFoundError as e:
        error_msg = f"✗ Error: {e}"
        if not quiet:
            click.echo(error_msg, err=True)
        return False, error_msg
    except ValueError as e:
        error_msg = f"✗ Error processing {filepath}: {e}"
        if not quiet:
            click.echo(error_msg, err=True)
        return False, error_msg
    except Exception as e:
        error_msg = f"✗ Unexpected error processing {filepath}: {e}"
        if not quiet:
            click.echo(error_msg, err=True)
        return False, error_msg


def collect_files(file_patterns: List[str]) -> List[Path]:
    """Collect all PNG files from the given patterns.

    Args:
        file_patterns: List of file paths or glob patterns

    Returns:
        List of Path objects for PNG files to process
    """
    files_to_process = []

    for file_pattern in file_patterns:
        file_path = Path(file_pattern)

        if "*" in file_pattern or "?" in file_pattern:
            # Handle glob patterns
            parent = file_path.parent if file_path.parent != Path(".") else Path.cwd()
            pattern = file_path.name
            matching_files = list(parent.glob(pattern))

            if not matching_files:
                click.echo(f"✗ No files matched pattern: {file_pattern}", err=True)
                continue

            # Filter for PNG files only
            for matched_file in matching_files:
                if matched_file.suffix.lower() == ".png":
                    files_to_process.append(matched_file)
        else:
            # Single file
            files_to_process.append(file_path)

    return files_to_process


def show_file_info(filepath: Path) -> None:
    """Display EXIF and file date information for a PNG file.

    Args:
        filepath: Path to the PNG file
    """
    try:
        handler = PNGHandler(filepath)

        # Get EXIF dates
        exif_dates = handler.get_exif_dates()

        # Get file timestamps
        mod_time = handler.get_modification_time()

        # Print information nicely
        click.echo(f"\n{'='*60}")
        click.echo(f"File: {filepath}")
        click.echo(f"{'='*60}")

        click.echo("\nEXIF Date Fields:")
        click.echo("-" * 40)
        for key, value in exif_dates.items():
            if value:
                click.echo(f"  {key:20s}: {value}")
            else:
                click.echo(f"  {key:20s}: (not set)")

        click.echo("\nFile Timestamps:")
        click.echo("-" * 40)
        click.echo(f"  {'Modification Time':20s}: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")

        click.echo()

    except FileNotFoundError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        sys.exit(1)


@click.group()
def main() -> None:
    """A photo tagging utility for adding EXIF date information to PNG files.

    \b
    Examples:
      phototag --date="20251103" my-photo.png
      phototag --date="mod" my-photo.png
      phototag --date="mod" *.png
      phototag show my-image.png
    """
    pass


@main.command(name="show")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
def show_command(files: Tuple[str, ...]) -> None:
    """Display EXIF date fields and file timestamps for PNG files.

    \b
    Examples:
      phototag show my-image.png
      phototag show image1.png image2.png
    """
    for file_path in files:
        show_file_info(Path(file_path))


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable units.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted string with appropriate unit (B, KB, MB, GB, TB)
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            if unit == 'B':
                return f"{size_bytes:.0f}{unit}"
            else:
                return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"


@main.command(name="ls")
@click.option("-l", is_flag=True, help="Long format (default, option ignored)")
@click.option("-t", is_flag=True, help="Sort by time (default, option ignored)")
@click.option("-r", "--reverse", is_flag=True, help="Reverse sort order (oldest last)")
@click.argument("files", nargs=-1, required=True, type=click.Path())
def ls_command(l: bool, t: bool, reverse: bool, files: Tuple[str, ...]) -> None:
    """List date information for PNG files in a columnar format.

    Files are sorted by EXIF DateTime (oldest first) by default.
    Use -r to reverse the order (oldest last).

    \b
    Examples:
      phototag ls *.png
      phototag ls -r *.png
      phototag ls -ltr *.png  (same as -r)
    """
    # Collect all files to process
    files_to_process = collect_files(list(files))

    if not files_to_process:
        click.echo("✗ No valid PNG files to process", err=True)
        sys.exit(1)

    # Collect information for all files
    file_info = []
    for filepath in files_to_process:
        try:
            handler = PNGHandler(filepath)

            # Get file size
            file_size = filepath.stat().st_size
            size_str = format_file_size(file_size)

            # Get EXIF DateTime
            exif_dates = handler.get_exif_dates()
            exif_datetime = exif_dates.get("DateTime", "(not set)")

            # Parse EXIF DateTime for sorting
            exif_datetime_parsed = None
            if exif_datetime and exif_datetime != "(not set)":
                exif_datetime_parsed = handler.parse_exif_datetime(exif_datetime)

            # Get file modification time
            mod_time = handler.get_modification_time()
            mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")

            file_info.append({
                "path": str(filepath),
                "size": size_str,
                "exif_datetime": exif_datetime if exif_datetime else "(not set)",
                "exif_datetime_parsed": exif_datetime_parsed,
                "mod_time": mod_time_str
            })
        except Exception as e:
            # Include files with errors in the output
            file_info.append({
                "path": str(filepath),
                "size": "(error)",
                "exif_datetime": f"(error: {e})",
                "exif_datetime_parsed": None,
                "mod_time": "(error)"
            })

    if not file_info:
        click.echo("✗ No files to display", err=True)
        sys.exit(1)

    # Sort by EXIF DateTime (oldest first by default)
    # Files without EXIF DateTime are placed at the end
    def sort_key(info):
        if info["exif_datetime_parsed"]:
            return (0, info["exif_datetime_parsed"])
        else:
            # Put files without EXIF DateTime at the end
            # Use a far future date as sort key
            return (1, datetime(9999, 12, 31))

    file_info.sort(key=sort_key, reverse=reverse)

    # Calculate column widths
    max_path_len = max(len(info["path"]) for info in file_info)
    max_size_len = max(len(info["size"]) for info in file_info)
    max_exif_len = max(len(info["exif_datetime"]) for info in file_info)
    max_mod_len = max(len(info["mod_time"]) for info in file_info)

    # Ensure minimum column widths for headers
    path_width = max(max_path_len, len("Path"))
    size_width = max(max_size_len, len("Size"))
    exif_width = max(max_exif_len, len("EXIF DateTime"))
    mod_width = max(max_mod_len, len("File Modified"))

    # Print header
    header = f"{'Path':<{path_width}}  {'Size':>{size_width}}  {'EXIF DateTime':<{exif_width}}  {'File Modified':<{mod_width}}"
    click.echo(header)
    click.echo("-" * len(header))

    # Print file information
    for info in file_info:
        line = f"{info['path']:<{path_width}}  {info['size']:>{size_width}}  {info['exif_datetime']:<{exif_width}}  {info['mod_time']:<{mod_width}}"
        click.echo(line)


@main.command(name="sync")
@click.argument("files", nargs=-1, required=True, type=click.Path())
def sync_command(files: Tuple[str, ...]) -> None:
    """Synchronize all date/time fields using the oldest date found.

    Reads EXIF DateTime (preferred) or CreateDate and file modification time,
    finds the oldest date, and sets all date/time fields to match.

    \b
    Examples:
      phototag sync my-photo.png
      phototag sync *.png
    """
    # Collect all files to process
    files_to_process = collect_files(list(files))

    if not files_to_process:
        click.echo("✗ No valid PNG files to process", err=True)
        sys.exit(1)

    # Process files with progress bar if multiple files
    success_count = 0
    error_count = 0

    # Use tqdm progress bar for multiple files
    use_progress = len(files_to_process) > 1

    # Start timing
    start_time = time.time()

    if use_progress:
        # With progress bar, suppress per-file messages
        with tqdm(total=len(files_to_process), desc="Syncing files", unit="file") as pbar:
            for filepath in files_to_process:
                try:
                    handler = PNGHandler(filepath)
                    oldest_date = handler.get_oldest_date()

                    # Set EXIF date and file timestamps to the oldest date
                    handler.set_exif_date(oldest_date)
                    handler.set_file_timestamps(oldest_date)

                    success_count += 1
                except Exception as e:
                    error_msg = f"✗ Error syncing {filepath}: {e}"
                    tqdm.write(error_msg)
                    error_count += 1
                pbar.update(1)
    else:
        # Single file, show normal output
        for filepath in files_to_process:
            try:
                handler = PNGHandler(filepath)
                oldest_date = handler.get_oldest_date()

                click.echo(f"Found oldest date for {filepath}: {oldest_date.strftime('%Y-%m-%d %H:%M:%S')}")

                # Set EXIF date and file timestamps to the oldest date
                handler.set_exif_date(oldest_date)
                handler.set_file_timestamps(oldest_date)

                click.echo(f"✓ Successfully synced {filepath}")
                success_count += 1
            except Exception as e:
                click.echo(f"✗ Error syncing {filepath}: {e}", err=True)
                error_count += 1

    # Calculate elapsed time
    elapsed_time = time.time() - start_time

    # Print summary
    click.echo(f"\nSynced {success_count} file(s) successfully", nl=False)
    if error_count > 0:
        click.echo(f", {error_count} error(s)", nl=False)

    # Add timing statistics for multiple files
    if use_progress:
        total_files = success_count + error_count
        if elapsed_time >= 1.0:
            # Show files per second for longer operations
            files_per_sec = total_files / elapsed_time
            click.echo(f" in {elapsed_time:.2f}s ({files_per_sec:.2f} files/sec)")
        else:
            # Show seconds per file for very fast operations
            sec_per_file = elapsed_time / total_files if total_files > 0 else 0
            click.echo(f" in {elapsed_time:.3f}s ({sec_per_file:.3f}s per file)")
    else:
        click.echo()

    if error_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


@main.command(name="tag", context_settings={"ignore_unknown_options": True})
@click.option(
    "--date",
    required=True,
    help='Date in YYYYMMDD format or "mod" to use file modification time',
)
@click.argument("files", nargs=-1, required=True, type=click.Path())
def tag_command(date: str, files: Tuple[str, ...]) -> None:
    """Set EXIF date information and file timestamps for PNG files.

    \b
    Examples:
      phototag tag --date="20251103" my-photo.png
      phototag tag --date="mod" my-photo.png
      phototag tag --date="mod" *.png
    """
    # Collect all files to process
    files_to_process = collect_files(list(files))

    if not files_to_process:
        click.echo("✗ No valid PNG files to process", err=True)
        sys.exit(1)

    # Process files with progress bar if multiple files
    success_count = 0
    error_count = 0

    # Use tqdm progress bar for multiple files
    use_progress = len(files_to_process) > 1

    # Start timing
    start_time = time.time()

    if use_progress:
        # With progress bar, suppress per-file messages
        with tqdm(total=len(files_to_process), desc="Processing files", unit="file") as pbar:
            for filepath in files_to_process:
                success, msg = process_file(filepath, date, quiet=True)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    # Show errors even with progress bar
                    tqdm.write(msg)
                pbar.update(1)
    else:
        # Single file, show normal output
        for filepath in files_to_process:
            success, msg = process_file(filepath, date, quiet=False)
            if success:
                success_count += 1
            else:
                error_count += 1

    # Calculate elapsed time
    elapsed_time = time.time() - start_time

    # Print summary
    click.echo(f"\nProcessed {success_count} file(s) successfully", nl=False)
    if error_count > 0:
        click.echo(f", {error_count} error(s)", nl=False)

    # Add timing statistics for multiple files
    if use_progress:
        total_files = success_count + error_count
        if elapsed_time >= 1.0:
            # Show files per second for longer operations
            files_per_sec = total_files / elapsed_time
            click.echo(f" in {elapsed_time:.2f}s ({files_per_sec:.2f} files/sec)")
        else:
            # Show seconds per file for very fast operations
            sec_per_file = elapsed_time / total_files if total_files > 0 else 0
            click.echo(f" in {elapsed_time:.3f}s ({sec_per_file:.3f}s per file)")
    else:
        click.echo()

    if error_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


# Make the default command 'tag' for backward compatibility
@main.result_callback()
@click.pass_context
def process_result(ctx: click.Context, result, **kwargs):
    """Handle the case where phototag is called with --date directly (backward compat)."""
    pass


# Override main to support legacy invocation (phototag --date="20251103" file.png)
_original_main = main


def main_with_compat():
    """Entry point with backward compatibility for legacy command format."""
    import sys as _sys

    # Check if this is a legacy invocation (--date without subcommand)
    if len(_sys.argv) > 1:
        # If first arg is --date (or starts with --date=), inject 'tag' command
        if (_sys.argv[1].startswith('--date') or
            (len(_sys.argv) > 2 and _sys.argv[1].startswith('-') and '--date' in _sys.argv[1:3])):
            # This is legacy format, insert 'tag' command
            _sys.argv.insert(1, 'tag')
        # If first arg is not a known subcommand and contains --date somewhere, inject 'tag'
        elif '--date' in _sys.argv and _sys.argv[1] not in ['show', 'tag', '--help', '-h']:
            # Insert 'tag' command after program name
            _sys.argv.insert(1, 'tag')

    _original_main()


if __name__ == "__main__":
    main_with_compat()
