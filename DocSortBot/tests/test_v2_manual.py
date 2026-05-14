from pathlib import Path
from docsortbot.sorter import sort_file

import os
os.system("rm -rf /tmp/Test_V2")
os.system("mkdir -p /tmp/Test_V2")
file_path = Path("/tmp/Test_V2/My_Statement.txt")
file_path.write_text("Statement Period: Jan 1 - Jan 31, 2021\nCopyright 2020.")

print("Running sort_file...")
sort_file(file_path, Path("/tmp/Test_V2"))

os.system("ls -R /tmp/Test_V2")
