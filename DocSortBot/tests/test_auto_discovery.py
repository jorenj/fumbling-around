import subprocess
import os
import json
from pathlib import Path

# Clean up
os.system("rm -rf ~/.docsortbot_config")
os.system("rm -rf ~/Statements")
os.system("rm -rf ~/Downloads/Statements")
os.system("mkdir -p ~/Downloads/Statements")

import time
print("Waiting for Spotlight to index...")
time.sleep(5)

print("Running docsortbot without args...")
p = subprocess.run([".venv/bin/docsortbot", "--dry-run"], capture_output=True, text=True)
print("Output:", p.stdout)
print("Error:", p.stderr)

config_file = Path.home() / ".docsortbot_config"
if config_file.exists():
    print("Saved config:", config_file.read_text())
else:
    print("No config file found.")
