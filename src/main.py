import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    
    # Set application-wide icon
    icon_path = get_resource_path(os.path.join("src", "icon.png"))
    if not os.path.exists(icon_path):
        # Fallback for running from src directory
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()