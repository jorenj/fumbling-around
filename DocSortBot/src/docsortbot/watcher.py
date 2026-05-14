import time
import uuid
import re
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .sorter import sort_file

def ensure_log_id(base_dir: Path) -> str:
    log_file = base_dir / "sort_log.txt"
    if log_file.exists():
        content = log_file.read_text()
        match = re.search(r'DocSortBotTrackerID_[a-f0-9\-]+', content)
        if match:
            return match.group(0)
            
    # if not found or file doesn't exist, generate one
    base_dir.mkdir(parents=True, exist_ok=True)
    new_id = f"DocSortBotTrackerID_{uuid.uuid4()}"
    with open(log_file, "a") as f:
        f.write(f"# {new_id}\n")
    return new_id

class StatementHandler(FileSystemEventHandler):
    def __init__(self, base_dir: Path, dry_run: bool):
        self.base_dir = base_dir
        self.dry_run = dry_run

    def on_created(self, event):
        if not event.is_directory:
            time.sleep(0.5)
            file_path = Path(event.src_path)
            if file_path.parent == self.base_dir:
                sort_file(file_path, self.base_dir, self.dry_run)

    def on_moved(self, event):
        if not event.is_directory:
            file_path = Path(event.dest_path)
            if file_path.parent == self.base_dir:
                sort_file(file_path, self.base_dir, self.dry_run)

def start_watching(base_dir: Path, dry_run: bool):
    tracker_id = ensure_log_id(base_dir)
    print(f"Folder Tracker ID: {tracker_id}")
    
    observer = Observer()
    event_handler = StatementHandler(base_dir, dry_run)
    observer.schedule(event_handler, str(base_dir), recursive=False)
    
    print(f"Monitoring '{base_dir}' for new files...")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
            if not base_dir.exists():
                print(f"\n[Warning] The monitored directory '{base_dir}' was moved or deleted.")
                print(f"Searching for folder via Spotlight using ID: {tracker_id}...")
                
                observer.stop()
                observer.join()
                
                found_new_path = False
                for _ in range(30):
                    time.sleep(2)
                    result = subprocess.run(["mdfind", tracker_id], capture_output=True, text=True)
                    paths = [p for p in result.stdout.strip().split('\n') if p and p.endswith('sort_log.txt')]
                    
                    if paths:
                        possible_new_dir = Path(paths[0]).parent
                        if possible_new_dir.exists():
                            print(f"\n[Success] Found folder at new location: {possible_new_dir}")
                            base_dir = possible_new_dir
                            
                            print("Scanning new location for unsorted files...")
                            for item in base_dir.iterdir():
                                if item.is_file():
                                    sort_file(item, base_dir, dry_run)
                                    
                            observer = Observer()
                            event_handler = StatementHandler(base_dir, dry_run)
                            observer.schedule(event_handler, str(base_dir), recursive=False)
                            observer.start()
                            print(f"Resumed monitoring at '{base_dir}'")
                            found_new_path = True
                            break
                            
                if not found_new_path:
                    print("[Error] Could not find the folder via Spotlight. Shutting down gracefully.")
                    break
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        observer.stop()
        observer.join()
