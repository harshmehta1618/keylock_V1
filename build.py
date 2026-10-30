import os
import subprocess
import sys

command = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--clean",
    "--name=keylock",
    "--onefile",
    f"--add-data=assets{os.pathsep}assets",
    "--noconsole",
    "--exclude-module=numpy",
    "main.py",
]

if sys.platform == "win32":
    command.insert(-1, "--icon=assets/icon.ico")

subprocess.run(command, check=True)
