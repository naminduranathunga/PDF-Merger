import PyInstaller.__main__
import os
import sys
import subprocess

def find_iscc():
    """Try to find the Inno Setup Compiler executable."""
    # Common installation paths
    paths = [
        os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Inno Setup 6", "ISCC.exe"),
        os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Inno Setup 6", "ISCC.exe"),
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    # Try to find in PATH
    try:
        subprocess.run(["ISCC", "/?"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "ISCC"
    except FileNotFoundError:
        return None

def build():
    # Define paths
    entry_point = os.path.join("src", "main.py")
    icon_path = os.path.join("src", "icon.png")
    
    # PyInstaller arguments
    args = [
        entry_point,
        "--name=PDFMerger",
        "--onefile",
        "--windowed", # No console window
        "--clean",
    ]
    
    # Add icon if it exists
    if os.path.exists(icon_path):
        args.append(f"--icon={icon_path}")
        # Add-data format is "source;dest" on Windows
        args.append(f"--add-data={icon_path};src")

    user_guide_path = os.path.join("src", "user_guide.pdf")
    if os.path.exists(user_guide_path):
        args.append(f"--add-data={user_guide_path};src")
    
    print(f"Starting PyInstaller build with args: {' '.join(args)}")
    PyInstaller.__main__.run(args)
    print("\nPyInstaller build complete!")

    # Try to run Inno Setup
    iscc_path = find_iscc()
    if iscc_path:
        print(f"\nFound Inno Setup at: {iscc_path}")
        print("Starting installer creation...")
        try:
            iss_file = "installer_setup.iss"
            subprocess.run([iscc_path, iss_file], check=True)
            print(f"\nInstaller created successfully! Check the 'installer' folder.")
        except subprocess.CalledProcessError as e:
            print(f"\nError running Inno Setup: {e}")
    else:
        print("\nInno Setup (ISCC.exe) not found. Skipping installer creation.")
        print("To create an installer, please install Inno Setup 6: https://jrsoftware.org/isdl.php")

if __name__ == "__main__":
    # Ensure we are in the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    build()
