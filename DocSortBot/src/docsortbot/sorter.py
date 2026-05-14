import os
import re
import shutil
from datetime import datetime
from pathlib import Path

from .extractor import extract_text_from_file, determine_year_from_text
from .db import init_db, log_to_db

# Regex to find 4-digit years starting with 19 or 20, not surrounded by other digits
YEAR_REGEX = re.compile(r'(?<!\d)(?:19|20)\d{2}(?!\d)')
# Matches the auto-added prefix like "[2023]_"
AUTO_PREFIX_REGEX = re.compile(r'^\[((?:19|20)\d{2})\]_')

def extract_year(filename: str, file_path: Path) -> tuple:
    """
    Returns a tuple (year, was_auto_extracted, evaluation_rule).
    Checks if already auto-renamed. If not, extracts from content. 
    Falls back to filename analysis if content extraction fails.
    """
    # If already auto-renamed, trust the filename
    match = AUTO_PREFIX_REGEX.match(filename)
    if match:
        return match.group(1), False, "Auto-Renamed Prefix"
        
    # 1. Filename Priority
    matches = YEAR_REGEX.findall(filename)
    unique_years = set(matches)
    if len(unique_years) == 1:
        return unique_years.pop(), False, "Filename Match"
        
    # 2. Content Fallback
    print(f"Reading content of '{filename}'...")
    text = extract_text_from_file(file_path)
    content_year, rule = determine_year_from_text(text)
    
    if content_year:
        return content_year, True, rule
        
    return None, False, None

def log_action(log_file: Path, filename: str, new_filename: str, destination_folder: str):
    """Appends an action to the living log file."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{now}] Moved '{filename}' to '{destination_folder}{new_filename}'\n"
    with open(log_file, "a") as f:
        f.write(log_entry)

def sort_file(file_path: Path, base_dir: Path, dry_run: bool = False):
    """
    Determines if a file should be moved, renames if necessary, and moves it.
    """
    # Only process actual files
    if not file_path.is_file():
        return
        
    filename = file_path.name
    
    # Ignore the log files
    if filename in ["sort_log.txt", "sort_log.db"]:
        return
        
    year, was_auto_extracted, rule = extract_year(filename, file_path)
    if not year:
        # No year found, leave it in the main folder
        return

    new_filename = filename
    if was_auto_extracted and not AUTO_PREFIX_REGEX.match(filename):
        new_filename = f"[{year}]_{filename}"

    dest_folder = base_dir / year
    dest_path = dest_folder / new_filename
    
    # Avoid overwriting existing files
    if dest_path.exists():
        print(f"File '{new_filename}' already exists in {year}/, skipping.")
        return

    print(f"{'[DRY RUN] ' if dry_run else ''}Moving '{filename}' -> {year}/{new_filename} (Rule: {rule})")
    
    if not dry_run:
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.move(str(file_path), str(dest_path))
            log_file = base_dir / "sort_log.txt"
            log_action(log_file, filename, new_filename, f"{year}/")
            
            # Log to SQLite
            init_db(base_dir)
            log_to_db(base_dir, filename, new_filename, f"{year}/", year, rule)
            
        except Exception as e:
            print(f"Error moving '{filename}': {e}")
