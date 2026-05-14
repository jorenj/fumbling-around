import subprocess
import time
import os

os.system("rm -rf ~/Statements_Test")
os.system("mkdir -p ~/Statements_Test")
os.system("touch ~/Statements_Test/Statement_2023.pdf")
os.system("touch ~/Statements_Test/2024-01-Statement.csv")
os.system("touch ~/Statements_Test/Receipt_1999_12_31.png")
os.system("touch ~/Statements_Test/Statement.pdf")
os.system("touch ~/Statements_Test/Statement_2023_2024.pdf")

print("Running docsortbot...")
p = subprocess.Popen([".venv/bin/docsortbot", "--path", os.path.expanduser("~/Statements_Test")])
time.sleep(2)

print("\nCreating a new file to test watcher...")
os.system("touch ~/Statements_Test/Late_Statement_2021.pdf")
time.sleep(3) # wait for watchdog to process

print("\nStopping docsortbot...")
p.terminate()
p.wait()

print("\nDirectory contents:")
os.system("ls -R ~/Statements_Test")
print("\nLog contents:")
os.system("cat ~/Statements_Test/sort_log.txt")
