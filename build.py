import subprocess
import shutil
import os
import sys
from pathlib import Path

def main():
    # Define the external files to copy
    external_files = [
        "config.json",
        "team1_template_nightelf.png",
        "team1_template_undead.png",
        "team1_template_human.png",
        "team1_template_orc.png",
        "icon.ico"
    ]
    
    # Define the PyInstaller command
    pyinstaller_command = [
        "pyinstaller",
        "--onefile",
        "--icon=icon.ico",
        "--add-data", "tesseract;tesseract",
        "--add-data", "data;data",
        "--exclude-module", "PyQt5",
        "gui.py"
    ]
    
    # Run PyInstaller
    print("Running PyInstaller...")
    result = subprocess.run(pyinstaller_command, capture_output=True, text=True)
    if result.returncode != 0:
        print("PyInstaller failed:")
        print(result.stdout)
        print(result.stderr)
        sys.exit(result.returncode)
    else:
        print("PyInstaller completed successfully.")
    
    # Define the dist folder
    dist_folder = Path("dist")
    if not dist_folder.exists():
        print("dist folder not found.")
        sys.exit(1)
    
    # Assume the executable is named 'gui.exe' on Windows or 'gui' on Unix
    if sys.platform.startswith("win"):
        exe_name = "gui.exe"
    else:
        exe_name = "gui"
    
    exe_path = dist_folder / exe_name
    if not exe_path.exists():
        print(f"Executable {exe_name} not found in dist folder.")
        sys.exit(1)
    
    # Copy external files to the dist folder
    for file in external_files:
        src = Path(file)
        if src.exists():
            shutil.copy(src, dist_folder / src.name)
            print(f"Copied {file} to dist folder.")
        else:
            print(f"External file {file} not found, skipping.")
    
    print("All external files copied to dist folder.")

if __name__ == "__main__":
    main()
