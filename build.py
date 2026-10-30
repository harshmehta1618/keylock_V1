import os
import subprocess
import sys

subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--name=keylock",
        "--onefile",
        f"--add-data=assets{os.pathsep}assets",
        "--noconsole",
        "--icon=assets/icon.ico",
        "--exclude-module=numpy",
        "main.py",
    ],
    check=True,
)
