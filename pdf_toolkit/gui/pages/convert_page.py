import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFileDialog, QScrollArea, QFrame, QProgressDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from gui.widgets.drop_zone import DropZone
from gui.styles.theme import ACCENT, TEXT_ON_ACCENT, SURFACE_ELEVATED, TEXT_SECONDARY, TEXT_PRIMARY, SURFACE, BORDER, SUCCESS, ERROR
from gui.utils.icons import get_icon

class ToolCard(QPushButton):
    """Compact tool card for the unified convert page."""
    def __init__(self, tool_id, title, icon_name, parent=None):
        super().__init__(parent)
        self.tool_id = tool_id
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon(icon_name, ACCENT, 24).pixmap(24, 24))
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 13px; border: none; background: transparent;")
        
        layout.addWidget(icon_lbl)
        layout.addSpacing(10)
        layout.addWidget(title_lbl)
        
        self.setFixedSize(140, 90)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        
        self.setStyleSheet(f"""
            ToolCard {{
                border: 1px solid {BORDER};
                border-radius: 8px;
                background-color: {SURFACE};
            }}
            ToolCard:hover {{
                background-color: {SURFACE_ELEVATED};
            }}
            ToolCard:checked {{
                border: 1px solid {ACCENT};
                background-color: {SURFACE_ELEVATED};
            }}
        """)

class UnifiedConvertPage(QWidget):
    """Unified convert page mimicking the new mockup design."""
    def __init__(self, tool_configs, parent=None):
        super().__init__(parent)
        self.tool_configs = tool_configs
        self.current_tool_id = None
        self.selected_files = []
        
        self._setup_ui()
        
        # Select first tool by default
        if self.tool_configs:
            self._on_tool_selected(self.tool_configs[0][0])
            
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        title = QLabel("Convert")
        title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 18px; font-weight: 500;")
        layout.addWidget(title)
        
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.cards = {}
        for t_id, title_text, exts, func, mode in self.tool_configs:
            icon_name = "pdf"
            if "word" in title_text.lower() or "docx" in t_id: icon_name = "word"
            elif "excel" in title_text.lower() or "xlsx" in t_id: icon_name = "excel"
            elif "powerpoint" in title_text.lower() or "ppt" in t_id: icon_name = "ppt"
            elif "image" in title_text.lower(): icon_name = "image"
            
            card = ToolCard(t_id, title_text, icon_name)
            card.clicked.connect(lambda checked=False, tid=t_id: self._on_tool_selected(tid))
            cards_layout.addWidget(card)
            self.cards[t_id] = card
            
        cards_layout.addStretch()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setFixedHeight(120)
        
        scroll_content = QWidget()
        scroll_content.setLayout(cards_layout)
        scroll.setWidget(scroll_content)
        
        layout.addWidget(scroll)
        
        # Drop Zone (integrated Convert button)
        self.drop_zone = DropZone()
        self.drop_zone.setMinimumHeight(250)
        self.drop_zone.files_dropped.connect(self._on_files_added)
        
        # Modify standard DropZone to match mockup
        # We need to add the Convert button INSIDE the drop zone layout
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setFixedSize(140, 40)
        self.convert_btn.setCursor(Qt.PointingHandCursor)
        self.convert_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT}; color: {TEXT_ON_ACCENT};
                font-size: 14px; font-weight: bold; border-radius: 6px; border: none;
            }}
            QPushButton:disabled {{
                background-color: {SURFACE_ELEVATED};
                color: {TEXT_SECONDARY};
            }}
        """)
        self.convert_btn.clicked.connect(self._on_convert)
        self.convert_btn.setEnabled(False)
        
        # Add an upload icon to the dropzone
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon("upload", TEXT_SECONDARY, 32).pixmap(32, 32))
        
        # Override dropzone layout
        # We'll just clear the existing layout and build ours
        old_layout = self.drop_zone.layout()
        if old_layout:
            QWidget().setLayout(old_layout) # delete old layout
            
        dz_layout = QVBoxLayout(self.drop_zone)
        dz_layout.setAlignment(Qt.AlignCenter)
        dz_layout.setSpacing(15)
        
        lbl = QLabel("Drop files here or browse")
        lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        
        dz_layout.addWidget(icon_lbl, alignment=Qt.AlignHCenter)
        dz_layout.addWidget(lbl, alignment=Qt.AlignHCenter)
        dz_layout.addWidget(self.convert_btn, alignment=Qt.AlignHCenter)
        
        # Clicking the drop zone itself triggers browse (except if clicking Convert btn)
        self.drop_zone.mousePressEvent = lambda e: self._on_browse() if e.pos().y() < self.convert_btn.geometry().top() else None
        
        layout.addWidget(self.drop_zone)
        
        # File list area (below dropzone)
        self.list_layout = QVBoxLayout()
        layout.addLayout(self.list_layout)
        
        layout.addStretch()

    def _on_tool_selected(self, tool_id: str):
        self.current_tool_id = tool_id
        for tid, card in self.cards.items():
            card.setChecked(tid == tool_id)
        # Clear files when switching tools to avoid extension mismatch
        self.selected_files = []
        self._refresh_file_list()

    def _get_current_tool_config(self):
        for cfg in self.tool_configs:
            if cfg[0] == self.current_tool_id:
                return cfg
        return None

    def _on_browse(self):
        cfg = self._get_current_tool_config()
        if not cfg: return
        exts = cfg[2]
        ext_filters = " ".join([f"*{ext}" for ext in exts])
        filter_str = f"Supported Files ({ext_filters});;All Files (*)"
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", filter_str)
        if files:
            self._on_files_added(files)

    def _on_files_added(self, files):
        cfg = self._get_current_tool_config()
        if not cfg: return
        accepted = [ext.lower() for ext in cfg[2]]
        
        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in accepted and file_path not in self.selected_files:
                self.selected_files.append(file_path)
                
        self._refresh_file_list()

    def _refresh_file_list(self):
        # Clear current list
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        for file_path in self.selected_files:
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 5, 10, 5)
            
            lbl = QLabel(os.path.basename(file_path))
            lbl.setStyleSheet(f"font-size: 13px; color: {TEXT_PRIMARY};")
            
            btn = QPushButton("✕")
            btn.setFixedSize(24, 24)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ color: {ERROR}; font-weight: bold; border: none; background: transparent; }}
                QPushButton:hover {{ background-color: {SURFACE_ELEVATED}; border-radius: 12px; }}
            """)
            btn.clicked.connect(lambda checked=False, p=file_path: self._remove_file(p))
            
            row_layout.addWidget(lbl)
            row_layout.addStretch()
            row_layout.addWidget(btn)
            row.setStyleSheet(f"QFrame {{ border-bottom: 1px solid {BORDER}; background-color: transparent; }}")
            
            self.list_layout.addWidget(row)
            
        self.convert_btn.setEnabled(len(self.selected_files) > 0)

    def _remove_file(self, file_path):
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
        self._refresh_file_list()

    def _on_convert(self):
        if not self.selected_files:
            return
            
        cfg = self._get_current_tool_config()
        if not cfg: return
        _, title, _, core_func, mode = cfg
            
        if mode == "independent":
            out_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
            if not out_path: return
        else:
            out_path, _ = QFileDialog.getSaveFileName(self, "Save Combined PDF", "", "PDF Files (*.pdf)")
            if not out_path: return
                
        progress = QProgressDialog("Processing...", None, 0, 0, self)
        progress.setWindowTitle("Converting")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        
        results = []
        if mode == "independent":
            for fpath in self.selected_files:
                try:
                    core_func(fpath, out_path)
                    results.append((fpath, True, ""))
                except Exception as e:
                    results.append((fpath, False, str(e)))
        else:
            try:
                core_func(self.selected_files, out_path)
                results.append(("Combined File", True, ""))
            except Exception as e:
                results.append(("Combined File", False, str(e)))
                
        progress.close()
        
        successes = sum(1 for r in results if r[1])
        failures = len(results) - successes
        msg = f"<p style='color: {TEXT_PRIMARY};'>Successfully processed: {successes}<br>Failed: {failures}</p>"
        
        if results:
            msg += "<ul style='list-style-type: none; padding-left: 0; margin-top: 10px;'>"
            for path, success, err_msg in results:
                fname = os.path.basename(path)
                if success:
                    indicator = f"<span style='color: {SUCCESS}; font-weight: bold;'>[✓]</span>"
                    row_text = f"<span style='color: {TEXT_PRIMARY};'> {fname}</span>"
                else:
                    indicator = f"<span style='color: {ERROR}; font-weight: bold;'>[✕]</span>"
                    row_text = f"<span style='color: {TEXT_SECONDARY};'> {fname} - {err_msg}</span>"
                msg += f"<li style='margin-bottom: 4px;'>{indicator}{row_text}</li>"
            msg += "</ul>"
            
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Conversion Complete")
        msg_box.setText(msg)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.exec()
