import subprocess
import time
import os

print("Setting up test folder in ~...")
os.system("rm -rf ~/Statements_Test_Recovery")
os.system("rm -rf ~/Statements_Test_Recovery_Moved")
os.system("mkdir -p ~/Statements_Test_Recovery")
os.system("touch ~/Statements_Test_Recovery/Statement_2023.pdf")

print("Starting docsortbot...")
p = subprocess.Popen([".venv/bin/docsortbot", "--path", os.path.expanduser("~/Statements_Test_Recovery")])
time.sleep(3)

print("\nMoving the folder...")
os.system("mv ~/Statements_Test_Recovery ~/Statements_Test_Recovery_Moved")

# Wait a bit for Spotlight to index and DocSortBot to find it
print("Waiting 15 seconds for Spotlight to index and DocSortBot to recover...")
time.sleep(15)

print("\nCreating new file in moved folder...")
os.system("touch ~/Statements_Test_Recovery_Moved/Statement_2024.pdf")

print("Waiting 5 seconds for watcher to process...")
time.sleep(5)

print("\nStopping docsortbot...")
p.terminate()
p.wait()

print("\nCheck output in new location:")
os.system("ls -R ~/Statements_Test_Recovery_Moved")
