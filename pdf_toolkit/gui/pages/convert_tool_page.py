import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFileDialog, QScrollArea, QFrame, QProgressDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from gui.widgets.drop_zone import DropZone

from core.utils import PDFToolkitError, ConversionError, InvalidFileError, LibreOfficeNotFoundError

class FileListItem(QFrame):
    """A row widget representing a selected file, with a remove button."""
    remove_clicked = Signal(str)
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        lbl = QLabel(os.path.basename(file_path))
        lbl.setStyleSheet("font-size: 13px;")
        
        btn = QPushButton("✕")
        btn.setFixedSize(24, 24)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { color: #d9534f; font-weight: bold; border: none; background: transparent; }
            QPushButton:hover { background-color: #f2dede; border-radius: 12px; }
        """)
        btn.clicked.connect(lambda: self.remove_clicked.emit(self.file_path))
        
        layout.addWidget(lbl)
        layout.addStretch()
        layout.addWidget(btn)
        
        self.setStyleSheet("FileListItem { border-bottom: 1px solid #e0e0e0; background-color: white; }")

class ConvertToolPage(QWidget):
    """
    A reusable page for any conversion tool.
    mode can be 'independent' (batch 1-to-1 processing) or 'combine' (N-to-1 processing).
    """
    back_clicked = Signal()
    
    def __init__(self, title: str, accepted_extensions: list, core_func: callable, mode: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.accepted_extensions = [ext.lower() for ext in accepted_extensions]
        self.core_func = core_func
        self.mode = mode  # "independent" or "combine"
        self.selected_files = []
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header (Back Button + Title)
        header_layout = QHBoxLayout()
        self.back_btn = QPushButton("← Back")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFixedSize(70, 30)
        self.back_btn.setStyleSheet("""
            QPushButton { border: none; color: #0078D7; font-size: 14px; font-weight: bold; text-align: left; }
            QPushButton:hover { text-decoration: underline; }
        """)
        self.back_btn.clicked.connect(self.back_clicked.emit)
        
        title_lbl = QLabel(self.title)
        title_lbl.setStyleSheet("font-size: 22px; font-weight: bold; margin-left: 10px;")
        
        header_layout.addWidget(self.back_btn)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Drop Zone
        self.drop_zone = DropZone()
        self.drop_zone.setMinimumHeight(150)
        self.drop_zone.browse_clicked.connect(self._on_browse)
        self.drop_zone.files_dropped.connect(self._on_files_added)
        layout.addWidget(self.drop_zone)
        
        # File List Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: 1px solid #ccc; border-radius: 4px; background: white; }")
        
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)
        self.scroll_area.setWidget(self.list_widget)
        
        layout.addWidget(self.scroll_area)
        
        # Convert Button
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setMinimumHeight(45)
        self.convert_btn.setCursor(Qt.PointingHandCursor)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D7; color: white;
                font-size: 16px; font-weight: bold; border-radius: 6px;
            }
            QPushButton:hover:enabled { background-color: #005A9E; }
            QPushButton:disabled { background-color: #a0a0a0; }
        """)
        self.convert_btn.clicked.connect(self._on_convert)
        self.convert_btn.setEnabled(False)
        
        layout.addWidget(self.convert_btn)
        
    def _on_browse(self):
        ext_filters = " ".join([f"*{ext}" for ext in self.accepted_extensions])
        filter_str = f"Supported Files ({ext_filters});;All Files (*)"
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", filter_str)
        if files:
            self._on_files_added(files)
            
    def _on_files_added(self, files):
        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in self.accepted_extensions and file_path not in self.selected_files:
                self.selected_files.append(file_path)
                self._add_file_ui(file_path)
        self._update_convert_btn()
        
    def _add_file_ui(self, file_path):
        item = FileListItem(file_path)
        item.remove_clicked.connect(self._on_file_removed)
        self.list_layout.addWidget(item)
        
    def _on_file_removed(self, file_path):
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
            
        for i in range(self.list_layout.count()):
            widget = self.list_layout.itemAt(i).widget()
            if isinstance(widget, FileListItem) and widget.file_path == file_path:
                widget.deleteLater()
                break
                
        self._update_convert_btn()
        
    def _update_convert_btn(self):
        self.convert_btn.setEnabled(len(self.selected_files) > 0)
        
    def _on_convert(self):
        if not self.selected_files:
            return
            
        # Get output path depending on mode
        if self.mode == "independent":
            out_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
            if not out_path:
                return
        else: # combine mode
            out_path, _ = QFileDialog.getSaveFileName(self, "Save Combined PDF", "", "PDF Files (*.pdf)")
            if not out_path:
                return
                
        # Show indeterminate progress dialog
        progress = QProgressDialog("Processing...", None, 0, 0, self)
        progress.setWindowTitle("Converting")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0) # show immediately
        progress.show()
        QApplication.processEvents() # Force paint before blocking loop
        
        results = []
        
        # Processing loop
        if self.mode == "independent":
            for fpath in self.selected_files:
                try:
                    self.core_func(fpath, out_path)
                    results.append((fpath, True, ""))
                except (PDFToolkitError, ConversionError, InvalidFileError, LibreOfficeNotFoundError, FileNotFoundError, ValueError) as e:
                    results.append((fpath, False, str(e)))
        else: # combine
            try:
                self.core_func(self.selected_files, out_path)
                results.append(("Combined File", True, ""))
            except (PDFToolkitError, ConversionError, InvalidFileError, LibreOfficeNotFoundError, FileNotFoundError, ValueError) as e:
                results.append(("Combined File", False, str(e)))
                
        progress.close()
        
        # Generate summary
        successes = sum(1 for r in results if r[1])
        failures = len(results) - successes
        
        msg = f"Successfully processed: {successes}\nFailed: {failures}\n"
        if failures > 0:
            msg += "\nErrors:\n"
            for path, success, err_msg in results:
                if not success:
                    msg += f"- {os.path.basename(path)}: {err_msg}\n"
                    
        QMessageBox.information(self, "Conversion Complete", msg)
