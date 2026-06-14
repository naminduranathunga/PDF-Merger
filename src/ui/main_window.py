from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QFileDialog, QMessageBox, QInputDialog, QStyle, QDialog,
    QFormLayout, QComboBox, QSpinBox, QCheckBox, QDoubleSpinBox, QGroupBox, QLabel
)
from PyQt6.QtCore import Qt, QSize, QUrl, QRectF, QThread
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor, QLinearGradient, QBrush, QDesktopServices, QFont, QPainter, QPen, QKeySequence
import os
from PyPDF2 import PdfReader, PdfWriter
from logic.pdf_layout import generate_n_up_pdf
from ui.about_dialog import AboutDialog
from ui.merge_progress_dialog import MergeProgressDialog
from ui.merge_worker import MergeWorker


def get_resource_path(relative_path):
    try:
        import sys
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)


class PdfListWidget(QListWidget):
    def __init__(self, add_paths_callback, parent=None):
        super().__init__(parent)
        self.add_paths_callback = add_paths_callback
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)

    def _extract_pdf_paths(self, event):
        pdf_paths = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue

            path = url.toLocalFile()
            if os.path.isfile(path) and path.lower().endswith(".pdf"):
                pdf_paths.append(path)

        return pdf_paths

    def dragEnterEvent(self, event):
        if event.source() is self:
            super().dragEnterEvent(event)
            return

        if self._extract_pdf_paths(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.source() is self:
            super().dragMoveEvent(event)
            return

        if self._extract_pdf_paths(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.source() is self:
            super().dropEvent(event)
            return

        pdf_paths = self._extract_pdf_paths(event)
        if not pdf_paths:
            event.ignore()
            return

        self.add_paths_callback(pdf_paths)
        event.acceptProposedAction()

class LayoutPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 300)
        self.options = {
            'cols': 2,
            'rows': 2,
            'page_size': (595, 842),
            'gap': 10,
            'margin': 20
        }

    def update_options(self, options):
        self.options.update(options)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Subtle background for the canvas
        painter.fillRect(self.rect(), QColor("#e8e8e8"))

        # Calculate page scale to fit widget
        w_width = self.width() - 40
        w_height = self.height() - 40
        
        pg_w, pg_h = self.options['page_size']
        scale = min(w_width / pg_w, w_height / pg_h)
        
        draw_w = pg_w * scale
        draw_h = pg_h * scale
        
        offset_x = (self.width() - draw_w) / 2
        offset_y = (self.height() - draw_h) / 2

        # Draw shadow
        painter.fillRect(QRectF(offset_x + 3, offset_y + 3, draw_w, draw_h), QColor(0, 0, 0, 40))

        # Draw the "Paper Sheet"
        page_rect = QRectF(offset_x, offset_y, draw_w, draw_h)
        painter.fillRect(page_rect, Qt.GlobalColor.white)
        painter.setPen(QPen(QColor("#888"), 1))
        painter.drawRect(page_rect)

        # Draw Grid Slots
        cols = self.options['cols']
        rows = self.options['rows']
        margin = self.options['margin'] * scale
        gap = self.options['gap'] * scale
        
        usable_w = draw_w - (2 * margin)
        usable_h = draw_h - (2 * margin)
        
        if cols > 0 and rows > 0:
            slot_w = (usable_w - (max(0, cols - 1)) * gap) / cols
            slot_h = (usable_h - (max(0, rows - 1)) * gap) / rows

            painter.setBrush(QBrush(QColor(56, 117, 215, 100))) # Transparent Aqua Blue
            painter.setPen(QPen(QColor("#3875d7"), 1, Qt.PenStyle.DashLine))

            for r in range(rows):
                for c in range(cols):
                    sx = offset_x + margin + c * (slot_w + gap)
                    sy = offset_y + margin + r * (slot_h + gap)
                    painter.drawRect(QRectF(sx, sy, slot_w, slot_h))

                    # Draw a mini representation of the source page orientation
                    painter.save()
                    is_h = self.options.get('source_is_horizontal', False)
                    p_margin = 4
                    p_w = (slot_w - p_margin * 2)
                    p_h = (slot_h - p_margin * 2)
                    
                    if is_h:
                        if p_h > p_w * 0.7: # Still fit as H
                            p_h = p_w * 0.7
                    else:
                        if p_w > p_h * 0.7: # Still fit as V
                            p_w = p_h * 0.7

                    px = sx + (slot_w - p_w) / 2
                    py = sy + (slot_h - p_h) / 2
                    
                    painter.setBrush(QBrush(QColor(255, 255, 255, 150)))
                    painter.setPen(QPen(QColor("#3875d7"), 0.5))
                    painter.drawRect(QRectF(px, py, p_w, p_h))
                    
                    # Add some "text lines" to indicate orientation
                    painter.setPen(QPen(QColor("#ccc"), 0.5))
                    line_gap = 3
                    for i in range(1, int(p_h / line_gap)):
                        painter.drawLine(QRectF(px + 2, py + i * line_gap, p_w - 4, 0).topLeft(), 
                                         QRectF(px + 2, py + i * line_gap, p_w - 4, 0).topRight())
                    
                    painter.restore()

class MergeOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Output Masterpiece Options")
        self.setFixedWidth(650) # Increased for preview
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        left_layout = QVBoxLayout()
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Standard Merge (One page per sheet)", "Multi-Page Layout (N-up)"])
        left_layout.addWidget(QLabel("Merge Method:"))
        left_layout.addWidget(self.method_combo)

        # N-Up Options Group
        self.nup_group = QGroupBox("Layout Options")
        self.nup_group.setEnabled(False)
        form = QFormLayout(self.nup_group)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 10)
        self.cols_spin.setValue(2)
        form.addRow("Columns:", self.cols_spin)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 10)
        self.rows_spin.setValue(2)
        form.addRow("Rows:", self.rows_spin)

        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["A4 (595x842 pts)", "US Letter (612x792 pts)", "Legal (612x1008 pts)"])
        form.addRow("Output Page Size:", self.page_size_combo)

        self.gap_spin = QSpinBox()
        self.gap_spin.setRange(0, 100)
        self.gap_spin.setValue(10)
        form.addRow("Gap between pages (pts):", self.gap_spin)

        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 200)
        self.margin_spin.setValue(20)
        form.addRow("Page Margin (pts):", self.margin_spin)

        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems([
            "Vertical Source -> Vertical Dest",
            "Vertical Source -> Horizontal Dest",
            "Horizontal Source -> Vertical Dest",
            "Horizontal Source -> Horizontal Dest"
        ])
        form.addRow("Orientation:", self.orientation_combo)

        self.border_check = QCheckBox("Add separation border")
        form.addRow(self.border_check)

        left_layout.addWidget(self.nup_group)

        # Bottom buttons for left side
        btns = QHBoxLayout()
        ok_btn = QPushButton("Process")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        left_layout.addLayout(btns)

        main_layout.addLayout(left_layout, stretch=2)

        # Right side: Preview
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("<b>Grid Visualization:</b>"))
        self.preview_widget = LayoutPreviewWidget()
        right_layout.addWidget(self.preview_widget)
        main_layout.addLayout(right_layout, stretch=3)

        # Connections
        self.method_combo.currentIndexChanged.connect(self.on_method_changed)
        self.cols_spin.valueChanged.connect(self.refresh_preview)
        self.rows_spin.valueChanged.connect(self.refresh_preview)
        self.page_size_combo.currentIndexChanged.connect(self.refresh_preview)
        self.gap_spin.valueChanged.connect(self.refresh_preview)
        self.margin_spin.valueChanged.connect(self.refresh_preview)
        self.orientation_combo.currentIndexChanged.connect(self.refresh_preview)
        self.border_check.toggled.connect(self.refresh_preview)

    def on_method_changed(self, index):
        self.nup_group.setEnabled(index == 1)
        self.refresh_preview()

    def refresh_preview(self):
        options = self.get_options()
        # If standard merge, we just show a 1x1 grid or something simpler
        if not options['is_nup']:
            options.update({'cols': 1, 'rows': 1})
        
        # 0,1: Vertical Source, 2,3: Horizontal Source
        options['source_is_horizontal'] = (options.get('orientation_mode', 0) >= 2)
        self.preview_widget.update_options(options)

    def get_options(self):
        page_sizes = {0: (595, 842), 1: (612, 792), 2: (612, 1008)}
        w, h = page_sizes[self.page_size_combo.currentIndex()]
        
        orient = self.orientation_combo.currentIndex()
        if orient == 1 or orient == 3: # Horizontal Dest
            w, h = h, w

        return {
            'is_nup': self.method_combo.currentIndex() == 1,
            'cols': self.cols_spin.value(),
            'rows': self.rows_spin.value(),
            'page_size': (w, h),
            'gap': self.gap_spin.value(),
            'margin': self.margin_spin.value(),
            'orientation_mode': orient,
            'show_border': self.border_check.isChecked()
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Merger")
        self.setMinimumSize(700, 500)
        self.merge_thread = None
        self.merge_worker = None
        self.merge_progress_dialog = None

        # Set window icon
        # Try PyInstaller path first, then fallback to relative dev path
        icon_path = get_resource_path(os.path.join("src", "icon.png"))
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.png")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.init_ui()
        self.apply_aqua_theme()

    def init_ui(self):
        self.build_menu_bar()

        # Central widget with background
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralWidget")
        self.setCentralWidget(self.central_widget)

        # Main horizontal layout: Left = List, Right = Buttons
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # Left Column: List View
        self.list_widget = PdfListWidget(self.add_pdf_files)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        main_layout.addWidget(self.list_widget, stretch=3)

        # Right Column Container
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Helper to create buttons with icons
        def create_btn(text, icon_name, callback):
            btn = QPushButton(f" {text}")
            if icon_name:
                icon = self.style().standardIcon(icon_name)
                btn.setIcon(icon)
                btn.setIconSize(QSize(20, 20))
            btn.clicked.connect(callback)
            btn.setMinimumHeight(40)
            button_layout.addWidget(btn)
            return btn

        create_btn("Add PDF(s)", QStyle.StandardPixmap.SP_FileIcon, self.add_pdf)
        create_btn("Remove Selected", QStyle.StandardPixmap.SP_TrashIcon, self.remove_pdf)
        create_btn("Move Up", QStyle.StandardPixmap.SP_ArrowUp, self.move_pdf_up)
        create_btn("Move Down", QStyle.StandardPixmap.SP_ArrowDown, self.move_pdf_down)
        create_btn("Split PDF", QStyle.StandardPixmap.SP_FileDialogDetailedView, self.split_pdf)
        
        button_layout.addStretch() # Push merge buttons to bottom
        
        self.merge_btn = create_btn("Merge PDFs", QStyle.StandardPixmap.SP_DialogSaveButton, self.merge_pdfs_simple)
        self.merge_btn.setObjectName("mergeButton")

        self.merge_adv_btn = create_btn("Merge Advanced", QStyle.StandardPixmap.SP_DialogSaveButton, self.merge_pdfs_advanced)
        self.merge_adv_btn.setObjectName("mergeAdvancedButton")

        main_layout.addWidget(button_container, stretch=1)

    def build_menu_bar(self):
        file_menu = self.menuBar().addMenu("&File")

        clear_action = QAction("&Clear All", self)
        clear_action.setShortcut(QKeySequence("C"))
        clear_action.triggered.connect(self.clear_all)
        file_menu.addAction(clear_action)

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("X"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = self.menuBar().addMenu("&Help")

        guide_action = QAction("&User Guide", self)
        guide_action.setShortcut(QKeySequence("G"))
        guide_action.triggered.connect(self.open_user_guide)
        help_menu.addAction(guide_action)

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def apply_aqua_theme(self):
        # Aqua styling logic
        self.setStyleSheet("""
            QMainWindow {
                background-color: #d1d1d1;
            }
            QWidget#centralWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ececec, stop:0.05 #e1e1e1, stop:1 #b5b5b5);
            }
            QListWidget {
                background-color: white;
                border: 1px solid #999;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Lucida Grande', 'Segoe UI', sans-serif;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: #bad9ff; /* Light Blue selection */
                color: black;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #f0f7ff;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:0.05 #f9f9f9, 
                    stop:0.5 #f0f0f0, stop:0.51 #e0e0e0, 
                    stop:0.95 #d0d0d0, stop:1 #c0c0c0);
                border: 1px solid #8c8c8c;
                border-radius: 12px;
                padding: 5px 15px;
                font-family: 'Lucida Grande', sans-serif;
                font-size: 12px;
                color: #333;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:0.05 #fdfdfd, 
                    stop:0.5 #f5f5f5, stop:0.51 #e5e5e5, 
                    stop:0.95 #dadada, stop:1 #cbcbcb);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #a0a0a0, stop:1 #d0d0d0);
            }
            QPushButton#mergeButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #8ebdf0, stop:0.05 #70aff1, 
                    stop:0.5 #3875d7, stop:0.51 #2865c7, 
                    stop:0.95 #1855b7, stop:1 #0845a7);
                color: white;
                border: 1px solid #105a9b;
                font-weight: bold;
            }
            QPushButton#mergeButton:hover {
                 background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #aed5f8, stop:0.05 #90c5f8, 
                    stop:0.5 #5895f7, stop:0.51 #4885e7, 
                    stop:0.95 #3875d7, stop:1 #2865c7);
            }
            QPushButton#mergeAdvancedButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #a8e0a8, stop:0.05 #8cd58c, 
                    stop:0.5 #46a046, stop:0.51 #3a8a3a, 
                    stop:0.95 #2e742e, stop:1 #225e22);
                color: white;
                border: 1px solid #1a4d1a;
                font-weight: bold;
            }
            QPushButton#mergeAdvancedButton:hover {
                 background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #c8f0c8, stop:0.05 #a8e5a8, 
                    stop:0.5 #66c266, stop:0.51 #55b055, 
                    stop:0.95 #449e44, stop:1 #338c33);
            }
        """)

    def add_pdf(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF Files (*.pdf);;All Files (*)")
        self.add_pdf_files(files)

    def add_pdf_files(self, files):
        added_count = 0
        for f in files:
            try:
                reader = PdfReader(f)
                num_pages = len(reader.pages)
                item = QListWidgetItem(f"📄 {os.path.basename(f)} ({num_pages} pages)")
                item.setData(Qt.ItemDataRole.UserRole, {"path": f, "pages": (0, num_pages)})
                self.list_widget.addItem(item)
                added_count += 1
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not read {f}:\n{str(e)}")

        if files and added_count == 0:
            QMessageBox.warning(self, "PDF Drop", "No valid PDF files were added.")

    def clear_all(self):
        self.list_widget.clear()

    def open_user_guide(self):
        guide_path = get_resource_path(os.path.join("src", "user_guide.pdf"))
        if not os.path.exists(guide_path):
            QMessageBox.warning(self, "User Guide", "The user guide PDF could not be found.")
            return

        if not QDesktopServices.openUrl(QUrl.fromLocalFile(guide_path)):
            QMessageBox.warning(self, "User Guide", "Unable to open the user guide PDF.")

    def show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def _collect_merge_jobs(self):
        jobs = []
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            data = item.data(Qt.ItemDataRole.UserRole)
            jobs.append({
                "path": data["path"],
                "start": data["pages"][0],
                "end": data["pages"][1],
            })
        return jobs

    def _reset_merge_state(self):
        self.merge_btn.setEnabled(True)
        self.merge_adv_btn.setEnabled(True)
        self.merge_thread = None
        self.merge_worker = None
        self.merge_progress_dialog = None

    def _start_merge_worker(self, save_path, options):
        jobs = self._collect_merge_jobs()
        if not jobs:
            QMessageBox.warning(self, "Merge PDFs", "The list is empty. Add some PDFs first.")
            return

        self.merge_btn.setEnabled(False)
        self.merge_adv_btn.setEnabled(False)

        self.merge_progress_dialog = MergeProgressDialog(self)
        self.merge_progress_dialog.canceled.connect(self.cancel_merge)
        self.merge_progress_dialog.show()

        self.merge_thread = QThread(self)
        self.merge_worker = MergeWorker(jobs, save_path, options)
        self.merge_worker.moveToThread(self.merge_thread)

        self.merge_thread.started.connect(self.merge_worker.run)
        self.merge_worker.progressChanged.connect(self.merge_progress_dialog.set_progress)
        self.merge_worker.statusChanged.connect(self.merge_progress_dialog.set_status)
        self.merge_worker.finished.connect(self._on_merge_finished)
        self.merge_worker.error.connect(self._on_merge_error)
        self.merge_worker.canceled.connect(self._on_merge_canceled)

        self.merge_worker.finished.connect(self.merge_thread.quit)
        self.merge_worker.error.connect(self.merge_thread.quit)
        self.merge_worker.canceled.connect(self.merge_thread.quit)
        self.merge_thread.finished.connect(self.merge_thread.deleteLater)
        self.merge_thread.finished.connect(self._cleanup_after_merge)

        self.merge_thread.start()

    def cancel_merge(self):
        if self.merge_worker:
            self.merge_worker.request_cancel()
        if self.merge_progress_dialog:
            self.merge_progress_dialog.set_cancelling()

    def _cleanup_after_merge(self):
        if self.merge_progress_dialog:
            self.merge_progress_dialog.finish()

    def _on_merge_finished(self, output_path):
        if self.merge_progress_dialog:
            self.merge_progress_dialog.set_progress(100)
            self.merge_progress_dialog.finish()

        QMessageBox.information(self, "Success", f"Artifact created successfully!\n\nOpening the file now...")
        QDesktopServices.openUrl(QUrl.fromLocalFile(output_path))
        self._reset_merge_state()

    def _on_merge_canceled(self):
        if self.merge_progress_dialog:
            self.merge_progress_dialog.set_cancelling()
            self.merge_progress_dialog.finish()

        QMessageBox.information(self, "Merge PDFs", "Merge canceled.")
        self._reset_merge_state()

    def _on_merge_error(self, message):
        if self.merge_progress_dialog:
            self.merge_progress_dialog.finish()

        QMessageBox.critical(self, "Error", f"Failed to create the masterpiece:\n{message}")
        self._reset_merge_state()

    def remove_pdf(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))

    def move_pdf_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)

    def move_pdf_down(self):
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)

    def split_pdf(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "Split PDF", "Please select a PDF in the list to split.")
            return
            
        data = item.data(Qt.ItemDataRole.UserRole)
        path = data["path"]
        start, end = data["pages"]
        count = end - start
        
        if count <= 1:
            QMessageBox.warning(self, "Split PDF", "This segment only has one page and cannot be split further.")
            return

        split_at, ok = QInputDialog.getInt(self, "Split PDF", 
                                          f"Split '{os.path.basename(path)}' after page (1-{count-1}):", 
                                          value=count // 2, min=1, max=count-1)
        if ok:
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            
            # Part 1
            p1_start = start
            p1_end = start + split_at
            item1 = QListWidgetItem(f"✂️ {os.path.basename(path)} (Pages {p1_start+1}-{p1_end})")
            item1.setData(Qt.ItemDataRole.UserRole, {"path": path, "pages": (p1_start, p1_end)})
            
            # Part 2
            p2_start = start + split_at
            p2_end = end
            item2 = QListWidgetItem(f"✂️ {os.path.basename(path)} (Pages {p2_start+1}-{p2_end})")
            item2.setData(Qt.ItemDataRole.UserRole, {"path": path, "pages": (p2_start, p2_end)})
            
            self.list_widget.insertItem(row, item1)
            self.list_widget.insertItem(row + 1, item2)

    def merge_pdfs_simple(self):
        self.perform_merge(is_advanced=False)

    def merge_pdfs_advanced(self):
        self.perform_merge(is_advanced=True)

    def perform_merge(self, is_advanced=False):
        if self.list_widget.count() == 0:
            QMessageBox.warning(self, "Merge PDFs", "The list is empty. Add some PDFs first.")
            return

        options = {'is_nup': False}
        if is_advanced:
            options_dialog = MergeOptionsDialog(self)
            if options_dialog.exec() != QDialog.DialogCode.Accepted:
                return
            options = options_dialog.get_options()

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", "", "PDF Files (*.pdf)")
        if not save_path:
            return

        self._start_merge_worker(save_path, options)
