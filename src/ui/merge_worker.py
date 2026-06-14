import os

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyPDF2 import PdfReader, PdfWriter

from logic.merge_exceptions import MergeCancelledError
from logic.pdf_layout import generate_n_up_pdf


class MergeWorker(QObject):
    progressChanged = pyqtSignal(int)
    statusChanged = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    canceled = pyqtSignal()

    def __init__(self, jobs, output_path, options, parent=None):
        super().__init__(parent)
        self.jobs = jobs
        self.output_path = output_path
        self.options = options or {}
        self._cancel_requested = False

    def request_cancel(self):
        self._cancel_requested = True

    def _check_cancelled(self):
        if self._cancel_requested:
            raise MergeCancelledError()

    def _emit_progress(self, current, total, start_percent=0, span_percent=100, status=None):
        if total <= 0:
            percent = start_percent + span_percent
        else:
            percent = start_percent + int((current / total) * span_percent)
        self.progressChanged.emit(min(100, max(0, percent)))
        if status:
            self.statusChanged.emit(status)

    def _run_standard_merge(self):
        writer = PdfWriter()
        total_pages = sum(job["end"] - job["start"] for job in self.jobs)
        processed_pages = 0

        for job in self.jobs:
            self._check_cancelled()
            self.statusChanged.emit(f"Reading {os.path.basename(job['path'])}...")
            reader = PdfReader(job["path"])

            for page_num in range(job["start"], job["end"]):
                self._check_cancelled()
                writer.add_page(reader.pages[page_num])
                processed_pages += 1
                self._emit_progress(processed_pages, total_pages, 0, 100, f"Merging {os.path.basename(job['path'])}...")

        self._check_cancelled()
        self.statusChanged.emit("Writing output file...")
        with open(self.output_path, "wb") as output_file:
            writer.write(output_file)

    def _run_n_up_merge(self):
        writer = PdfWriter()
        total_pages = sum(job["end"] - job["start"] for job in self.jobs)
        processed_pages = 0

        self.statusChanged.emit("Collecting pages for layout...")
        for job in self.jobs:
            self._check_cancelled()
            reader = PdfReader(job["path"])
            for page_num in range(job["start"], job["end"]):
                self._check_cancelled()
                writer.add_page(reader.pages[page_num])
                processed_pages += 1
                self._emit_progress(processed_pages, total_pages, 0, 40, f"Collecting {os.path.basename(job['path'])}...")

        self._check_cancelled()

        def layout_progress(current, total, status=None):
            if total <= 0:
                percent = 100
            else:
                percent = 40 + int((current / total) * 60)
            self.progressChanged.emit(min(100, max(0, percent)))
            if status:
                self.statusChanged.emit(status)

        self.statusChanged.emit("Building N-up layout...")
        generate_n_up_pdf(
            writer,
            self.output_path,
            self.options,
            progress_callback=layout_progress,
            cancel_callback=lambda: self._cancel_requested,
        )

    @pyqtSlot()
    def run(self):
        try:
            self.progressChanged.emit(0)
            self.statusChanged.emit("Starting merge...")
            if self.options.get("is_nup", False):
                self._run_n_up_merge()
            else:
                self._run_standard_merge()
            self._check_cancelled()
            self.progressChanged.emit(100)
            self.finished.emit(self.output_path)
        except MergeCancelledError:
            self.canceled.emit()
        except Exception as exc:
            self.error.emit(str(exc))
