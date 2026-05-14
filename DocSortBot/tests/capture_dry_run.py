import subprocess
import os

print("Running DocSortBot in dry-run mode on your actual files...")
try:
    result = subprocess.run(
        [".venv/bin/docsortbot", "--dry-run"], 
        capture_output=True, 
        text=True, 
        timeout=15
    )
    print(result.stdout)
except subprocess.TimeoutExpired as e:
    # If it times out, it means it finished the batch sort and is now in the infinite watcher loop.
    if e.stdout:
        # Decode bytes if needed (subprocess.run with text=True might return string, but TimeoutExpired.stdout is bytes)
        out = e.stdout
        if isinstance(out, bytes):
            out = out.decode('utf-8', errors='ignore')
        print(out)
    else:
        print("Timed out, no output captured.")
