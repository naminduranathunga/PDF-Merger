from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout


class MergeProgressDialog(QDialog):
    canceled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Merging PDFs")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumWidth(420)
        self.setMinimumHeight(140)
        self.setModal(True)
        self._allow_close = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.status_label = QLabel("Preparing merge...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_requested)
        button_row.addWidget(self.cancel_button)

        layout.addLayout(button_row)

    def set_status(self, text):
        self.status_label.setText(text)

    def set_progress(self, value):
        self.progress_bar.setValue(value)

    def set_cancelling(self):
        self.status_label.setText("Cancelling merge...")
        self.cancel_button.setEnabled(False)

    def finish(self):
        self._allow_close = True
        super().accept()

    def cancel_requested(self):
        self.set_cancelling()
        self.canceled.emit()

    def closeEvent(self, event):
        if self._allow_close:
            super().closeEvent(event)
            return

        self.cancel_requested()
        event.ignore()
