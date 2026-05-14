import subprocess
import time
import os
import signal

os.system("rm -rf /tmp/watchdog_test")
os.system("mkdir -p /tmp/watchdog_test")

p = subprocess.Popen([".venv/bin/docsortbot", "--path", "/tmp/watchdog_test"])
time.sleep(2)

print("\nMoving the folder to simulate movement...")
os.system("mv /tmp/watchdog_test /tmp/watchdog_test_moved")

print("\nWaiting for docsortbot to gracefully exit...")
p.wait(timeout=5)
print(f"Docsortbot exited with code {p.returncode}")

print("\nCheck output")
os.system("ls -R /tmp/watchdog_test_moved")
