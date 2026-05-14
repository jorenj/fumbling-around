import argparse
import sys
import json
import subprocess
from pathlib import Path

from .sorter import sort_file
from .watcher import start_watching
from .web import start_server
import threading

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / ".docsortbot_config"

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def find_statements_via_spotlight():
    print("Searching your Mac for a 'Statements' folder using Spotlight...")
    query = 'kMDItemFSName == "Statements" && kMDItemContentType == "public.folder"'
    result = subprocess.run(["mdfind", query], capture_output=True, text=True)
    paths = [p for p in result.stdout.strip().split('\n') if p]
    return paths

def main():
    parser = argparse.ArgumentParser(description="DocSortBot: Monitor and sort statements by year.")
    parser.add_argument(
        "--path", 
        type=str, 
        default=None,
        help="Path to the statements folder to monitor. Will be saved for future runs."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without actually moving files or writing to the log."
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Run the live web dashboard concurrently on port 8000."
    )
    
    args = parser.parse_args()
    config = load_config()
    
    if args.path:
        base_dir = Path(args.path).expanduser().resolve()
        config['path'] = str(base_dir)
        save_config(config)
    elif 'path' in config:
        base_dir = Path(config['path'])
    else:
        # Default to ~/Statements
        base_dir = Path("~/Statements").expanduser().resolve()
        
    if not base_dir.exists():
        if args.path:
            # If the user explicitly provided a path and it doesn't exist, hard error.
            print(f"Error: The directory '{base_dir}' does not exist.")
            print("Please create it or specify a different path.")
            sys.exit(1)
        else:
            # We are using the default or saved path, and it doesn't exist. Try Spotlight.
            print(f"The directory '{base_dir}' does not exist.")
            paths = find_statements_via_spotlight()
            if not paths:
                print("Could not find any folder named 'Statements' via Spotlight.")
                print("Please create it or specify a path using --path.")
                sys.exit(1)
            elif len(paths) == 1:
                base_dir = Path(paths[0])
                print(f"Found exactly one 'Statements' folder: {base_dir}")
                print("Saving this as the new default path...")
                config['path'] = str(base_dir)
                save_config(config)
            else:
                print("Found multiple 'Statements' folders on your Mac:")
                for p in paths:
                    print(f" - {p}")
                print("\nPlease run the bot again and explicitly specify which one you want:")
                print(f"Example: docsortbot --path \"{paths[0]}\"")
                sys.exit(1)
        
    print(f"DocSortBot initialized.")
    print(f"Target directory: {base_dir}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'ACTIVE'}")
    print("-" * 30)
    
    # Process existing files first
    print("Scanning for existing files to sort...")
    for item in base_dir.iterdir():
        if item.is_file():
            sort_file(item, base_dir, args.dry_run)
            
    print("-" * 30)
            
    # Then start monitoring
    if args.dashboard:
        # Run watcher in a background thread
        watcher_thread = threading.Thread(target=start_watching, args=(base_dir, args.dry_run), daemon=True)
        watcher_thread.start()
        # Run the FastAPI server in the main thread
        start_server(base_dir, 8000)
    else:
        start_watching(base_dir, args.dry_run)

if __name__ == "__main__":
    main()
