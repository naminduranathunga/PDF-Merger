from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PyQt6.QtCore import Qt


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PDF Merger")
        self.setMinimumWidth(360)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("<h2>PDF Merger</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        description = QLabel(
            "<p>A simple desktop tool for organizing, splitting, and merging PDF files.</p>"
            "<p>Use the File menu to clear the list or exit, and the Help menu to open the user guide.</p>"
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        version = QLabel("Version 1.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
