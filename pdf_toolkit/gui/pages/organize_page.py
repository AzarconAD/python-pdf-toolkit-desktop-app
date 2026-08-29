import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QStackedWidget,
    QPushButton, QListWidget, QAbstractItemView, QListWidgetItem, QFileDialog, QProgressDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt

from gui.styles.theme import TEXT_SECONDARY, TEXT_PRIMARY, SURFACE, BORDER, ACCENT, TEXT_ON_ACCENT, SURFACE_ELEVATED, ERROR, SUCCESS
from gui.pages.convert_page import ToolCard
from gui.widgets.drop_zone import DropZone
from gui.utils.icons import get_icon
from PySide6.QtWidgets import QComboBox, QRadioButton, QSpinBox
from core.organize import merge_pdfs, extract_pages, delete_pages, reorder_pages, rotate_pages, split_pdf

class SplitToolWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_path = None
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.drop_zone = DropZone()
        self.drop_zone.setMinimumHeight(200)
        self.drop_zone.files_dropped.connect(self._on_files_added)
        
        dz_layout = QVBoxLayout(self.drop_zone)
        dz_layout.setAlignment(Qt.AlignCenter)
        dz_layout.setSpacing(15)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon("upload", TEXT_SECONDARY, 32).pixmap(32, 32))
        lbl = QLabel("Drop a single PDF here to Split")
        lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setFixedSize(120, 36)
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setStyleSheet(f"background-color: {SURFACE_ELEVATED}; color: {TEXT_PRIMARY}; border-radius: 6px; border: 1px solid {BORDER};")
        self.browse_btn.clicked.connect(self._on_browse)
        
        dz_layout.addWidget(icon_lbl, alignment=Qt.AlignHCenter)
        dz_layout.addWidget(lbl, alignment=Qt.AlignHCenter)
        dz_layout.addWidget(self.browse_btn, alignment=Qt.AlignHCenter)
        
        self.drop_zone.mousePressEvent = lambda e: self._on_browse() if e.pos().y() < self.browse_btn.geometry().top() else None
        
        self.active_container = QWidget()
        ac_layout = QVBoxLayout(self.active_container)
        ac_layout.setContentsMargins(0, 0, 0, 0)
        
        top_bar = QHBoxLayout()
        self.file_lbl = QLabel()
        self.file_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        
        self.change_file_btn = QPushButton("Change File")
        self.change_file_btn.setCursor(Qt.PointingHandCursor)
        self.change_file_btn.setStyleSheet(f"background-color: transparent; color: {TEXT_SECONDARY}; border: 1px solid {BORDER}; border-radius: 4px; padding: 4px 10px;")
        self.change_file_btn.clicked.connect(self._on_change_file)
        
        self.action_btn = QPushButton("Split PDF")
        self.action_btn.setFixedSize(140, 36)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ACCENT}; color: {TEXT_ON_ACCENT}; font-weight: bold; border-radius: 6px; border: none; }}
            QPushButton:disabled {{ background-color: {SURFACE_ELEVATED}; color: {TEXT_SECONDARY}; }}
        """)
        self.action_btn.clicked.connect(self._on_action)
        self.action_btn.setEnabled(False)
        
        top_bar.addWidget(self.file_lbl)
        top_bar.addStretch()
        top_bar.addWidget(self.change_file_btn)
        top_bar.addWidget(self.action_btn)
        
        ac_layout.addLayout(top_bar)
        
        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 10, 0, 10)
        
        self.radio_every_n = QRadioButton("Split every N pages")
        self.radio_every_n.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.radio_every_n.setChecked(True)
        self.radio_every_n.toggled.connect(self._update_action_btn)
        
        self.spin_n = QSpinBox()
        self.spin_n.setRange(1, 9999)
        self.spin_n.setValue(1)
        self.spin_n.setStyleSheet(f"background-color: {SURFACE_ELEVATED}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; border-radius: 4px;")
        
        self.radio_custom = QRadioButton("Custom ranges")
        self.radio_custom.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.radio_custom.toggled.connect(self._update_action_btn)
        
        options_layout.addWidget(self.radio_every_n)
        options_layout.addWidget(self.spin_n)
        options_layout.addSpacing(20)
        options_layout.addWidget(self.radio_custom)
        options_layout.addStretch()
        
        ac_layout.addLayout(options_layout)
        
        self.grid_wrapper = QVBoxLayout()
        ac_layout.addLayout(self.grid_wrapper)
        
        self.range_preview_lbl = QLabel("")
        self.range_preview_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 13px; margin: 5px;")
        self.range_preview_lbl.setAlignment(Qt.AlignCenter)
        self.range_preview_lbl.setVisible(False)
        ac_layout.addWidget(self.range_preview_lbl)
        
        self.stacked = QStackedWidget()
        self.stacked.addWidget(self.drop_zone)
        self.stacked.addWidget(self.active_container)
        
        self.layout.addWidget(self.stacked)
        
    def _on_browse(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf)")
        if file: self._load_file(file)
            
    def _on_files_added(self, files):
        for f in files:
            if f.lower().endswith('.pdf'):
                self._load_file(f)
                break
                
    def _load_file(self, file_path):
        self.pdf_path = file_path
        self.file_lbl.setText(os.path.basename(file_path))
        
        while self.grid_wrapper.count():
            item = self.grid_wrapper.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        from gui.widgets.page_thumbnail_grid import PageThumbnailGrid
        self.grid = PageThumbnailGrid(self.pdf_path)
        self.grid.selectionChanged.connect(self._update_action_btn)
        self.grid_wrapper.addWidget(self.grid)
        
        self._update_action_btn()
        self.stacked.setCurrentWidget(self.active_container)
        
    def _on_change_file(self):
        self.pdf_path = None
        self.stacked.setCurrentWidget(self.drop_zone)
        
    def _update_action_btn(self):
        if not hasattr(self, 'grid'):
            return
            
        is_custom = self.radio_custom.isChecked()
        self.spin_n.setEnabled(not is_custom)
        self.grid.setEnabled(is_custom) 
        
        self.range_preview_lbl.setVisible(is_custom)
        
        if is_custom:
            selected = sorted(self.grid.get_selected_pages())
            self.action_btn.setEnabled(len(selected) > 0)
            
            if not selected:
                self.range_preview_lbl.setText("Select pages to define split ranges.")
            else:
                ranges = []
                start = selected[0]
                end = selected[0]
                for p in selected[1:]:
                    if p == end + 1:
                        end = p
                    else:
                        ranges.append([start, end])
                        start = p
                        end = p
                ranges.append([start, end])
                
                range_strs = []
                for r in ranges:
                    if r[0] == r[1]:
                        range_strs.append(f"page {r[0]}")
                    else:
                        range_strs.append(f"pages {r[0]}-{r[1]}")
                
                file_word = "file" if len(ranges) == 1 else "files"
                self.range_preview_lbl.setText(f"Will create {len(ranges)} {file_word}: {', '.join(range_strs)}")
        else:
            self.action_btn.setEnabled(True)
            
    def _on_action(self):
        out_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not out_dir: return
        
        ranges = None
        pages_per_file = 1
        
        if self.radio_custom.isChecked():
            selected = sorted(self.grid.get_selected_pages())
            if not selected: return
            ranges = []
            start = selected[0]
            end = selected[0]
            for p in selected[1:]:
                if p == end + 1:
                    end = p
                else:
                    ranges.append([start, end])
                    start = p
                    end = p
            ranges.append([start, end])
        else:
            pages_per_file = self.spin_n.value()
            
        progress = QProgressDialog("Splitting PDF...", None, 0, 0, self)
        progress.setWindowTitle("Split PDF")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        
        try:
            split_pdf(self.pdf_path, out_dir, pages_per_file=pages_per_file, ranges=ranges)
            success, err_msg = True, ""
        except Exception as e:
            success, err_msg = False, str(e)
            
        progress.close()
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Split Complete")
        if success:
            msg_box.setText(f"<span style='color: {SUCCESS}; font-weight: bold;'>[✓]</span> Successfully split PDF into:<br>{out_dir}")
        else:
            msg_box.setText(f"<span style='color: {ERROR}; font-weight: bold;'>[✕]</span> Split failed:<br>{err_msg}")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.exec()

class ThumbnailActionToolWidget(QWidget):
    def __init__(self, action_name: str, core_func, mode="select", parent=None):
        super().__init__(parent)
        self.action_name = action_name
        self.core_func = core_func
        self.mode = mode
        self.pdf_path = None
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.drop_zone = DropZone()
        self.drop_zone.setMinimumHeight(200)
        self.drop_zone.files_dropped.connect(self._on_files_added)
        
        dz_layout = QVBoxLayout(self.drop_zone)
        dz_layout.setAlignment(Qt.AlignCenter)
        dz_layout.setSpacing(15)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon("upload", TEXT_SECONDARY, 32).pixmap(32, 32))
        lbl = QLabel(f"Drop a single PDF here to {self.action_name}")
        lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setFixedSize(120, 36)
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setStyleSheet(f"background-color: {SURFACE_ELEVATED}; color: {TEXT_PRIMARY}; border-radius: 6px; border: 1px solid {BORDER};")
        self.browse_btn.clicked.connect(self._on_browse)
        
        dz_layout.addWidget(icon_lbl, alignment=Qt.AlignHCenter)
        dz_layout.addWidget(lbl, alignment=Qt.AlignHCenter)
        dz_layout.addWidget(self.browse_btn, alignment=Qt.AlignHCenter)
        
        self.drop_zone.mousePressEvent = lambda e: self._on_browse() if e.pos().y() < self.browse_btn.geometry().top() else None
        
        self.active_container = QWidget()
        ac_layout = QVBoxLayout(self.active_container)
        ac_layout.setContentsMargins(0, 0, 0, 0)
        
        top_bar = QHBoxLayout()
        self.file_lbl = QLabel()
        self.file_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        
        self.change_file_btn = QPushButton("Change File")
        self.change_file_btn.setCursor(Qt.PointingHandCursor)
        self.change_file_btn.setStyleSheet(f"background-color: transparent; color: {TEXT_SECONDARY}; border: 1px solid {BORDER}; border-radius: 4px; padding: 4px 10px;")
        self.change_file_btn.clicked.connect(self._on_change_file)
        
        self.action_btn = QPushButton(self.action_name)
        self.action_btn.setFixedSize(140, 36)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ACCENT}; color: {TEXT_ON_ACCENT}; font-weight: bold; border-radius: 6px; border: none; }}
            QPushButton:disabled {{ background-color: {SURFACE_ELEVATED}; color: {TEXT_SECONDARY}; }}
        """)
        self.action_btn.clicked.connect(self._on_action)
        self.action_btn.setEnabled(False)
        
        top_bar.addWidget(self.file_lbl)
        top_bar.addStretch()
        
        if self.mode == "rotate":
            lbl_angle = QLabel("Angle:")
            lbl_angle.setStyleSheet(f"color: {TEXT_PRIMARY};")
            self.angle_combo = QComboBox()
            self.angle_combo.addItems(["90", "180", "270", "-90"])
            self.angle_combo.setStyleSheet(f"background-color: {SURFACE_ELEVATED}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; border-radius: 4px; padding: 4px;")
            top_bar.addWidget(lbl_angle)
            top_bar.addWidget(self.angle_combo)
            top_bar.addSpacing(10)
            
        top_bar.addWidget(self.change_file_btn)
        top_bar.addWidget(self.action_btn)
        
        ac_layout.addLayout(top_bar)
        
        if self.mode == "rotate":
            help_lbl = QLabel("Tip: Select specific pages to rotate, or select nothing to rotate all pages.")
            help_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; margin-bottom: 5px;")
            ac_layout.addWidget(help_lbl)
        elif self.mode == "reorder":
            help_lbl = QLabel("Tip: Drag and drop thumbnails to reorder pages.")
            help_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; margin-bottom: 5px;")
            ac_layout.addWidget(help_lbl)
            
        self.grid_wrapper = QVBoxLayout()
        ac_layout.addLayout(self.grid_wrapper)
        
        self.stacked = QStackedWidget()
        self.stacked.addWidget(self.drop_zone)
        self.stacked.addWidget(self.active_container)
        
        self.layout.addWidget(self.stacked)
        
    def _on_browse(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf)")
        if file: self._load_file(file)
            
    def _on_files_added(self, files):
        for f in files:
            if f.lower().endswith('.pdf'):
                self._load_file(f)
                break
                
    def _load_file(self, file_path):
        self.pdf_path = file_path
        self.file_lbl.setText(os.path.basename(file_path))
        
        while self.grid_wrapper.count():
            item = self.grid_wrapper.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        from gui.widgets.page_thumbnail_grid import PageThumbnailGrid
        self.grid = PageThumbnailGrid(self.pdf_path)
        self.grid.selectionChanged.connect(self._update_action_btn)
        self.grid_wrapper.addWidget(self.grid)
        
        self._update_action_btn()
        self.stacked.setCurrentWidget(self.active_container)
        
    def _on_change_file(self):
        self.pdf_path = None
        self.stacked.setCurrentWidget(self.drop_zone)
        
    def _update_action_btn(self):
        if hasattr(self, 'grid'):
            if self.mode == "select":
                self.action_btn.setEnabled(len(self.grid.get_selected_pages()) > 0)
            else:
                self.action_btn.setEnabled(True)
            
    def _on_action(self):
        args = []
        if self.mode == "select":
            selected = self.grid.get_selected_pages()
            if not selected: return
            args = [selected]
        elif self.mode == "reorder":
            order = self.grid.get_page_order()
            args = [order]
        elif self.mode == "rotate":
            selected = self.grid.get_selected_pages() or None
            angle = int(self.angle_combo.currentText())
            args = [angle, selected]
            
        out_path, _ = QFileDialog.getSaveFileName(self, f"Save {self.action_name} Result", f"{self.action_name.lower().replace(' ', '_')}.pdf", "PDF Files (*.pdf)")
        if not out_path: return
        
        progress = QProgressDialog(f"{self.action_name}...", None, 0, 0, self)
        progress.setWindowTitle(self.action_name)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        
        try:
            self.core_func(self.pdf_path, out_path, *args)
            success, err_msg = True, ""
        except Exception as e:
            success, err_msg = False, str(e)
            
        progress.close()
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"{self.action_name} Complete")
        if success:
            msg_box.setText(f"<span style='color: {SUCCESS}; font-weight: bold;'>[✓]</span> Successfully completed {self.action_name.lower()} into:<br>{os.path.basename(out_path)}")
        else:
            msg_box.setText(f"<span style='color: {ERROR}; font-weight: bold;'>[✕]</span> {self.action_name} failed:<br>{err_msg}")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.exec()

class MergeToolWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.drop_zone = DropZone()
        self.drop_zone.setMinimumHeight(200)
        self.drop_zone.files_dropped.connect(self._on_files_added)
        
        self.merge_btn = QPushButton("Merge PDFs")
        self.merge_btn.setFixedSize(140, 40)
        self.merge_btn.setCursor(Qt.PointingHandCursor)
        self.merge_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT}; color: {TEXT_ON_ACCENT};
                font-size: 14px; font-weight: bold; border-radius: 6px; border: none;
            }}
            QPushButton:disabled {{
                background-color: {SURFACE_ELEVATED};
                color: {TEXT_SECONDARY};
            }}
        """)
        self.merge_btn.clicked.connect(self._on_merge)
        self.merge_btn.setEnabled(False)
        
        old_layout = self.drop_zone.layout()
        if old_layout:
            QWidget().setLayout(old_layout)
            
        dz_layout = QVBoxLayout(self.drop_zone)
        dz_layout.setAlignment(Qt.AlignCenter)
        dz_layout.setSpacing(15)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon("upload", TEXT_SECONDARY, 32).pixmap(32, 32))
        lbl = QLabel("Drop PDF files here or browse")
        lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        
        dz_layout.addWidget(icon_lbl, alignment=Qt.AlignHCenter)
        dz_layout.addWidget(lbl, alignment=Qt.AlignHCenter)
        dz_layout.addWidget(self.merge_btn, alignment=Qt.AlignHCenter)
        
        self.drop_zone.mousePressEvent = lambda e: self._on_browse() if e.pos().y() < self.merge_btn.geometry().top() else None
        
        layout.addWidget(self.drop_zone)
        
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent; border: 1px solid {BORDER};
                border-radius: 4px; color: {TEXT_PRIMARY}; font-size: 13px; padding: 5px;
            }}
            QListWidget::item {{ padding: 8px; border-bottom: 1px solid {SURFACE_ELEVATED}; }}
            QListWidget::item:selected {{ background-color: {SURFACE_ELEVATED}; color: {ACCENT}; }}
        """)
        self.list_widget.keyPressEvent = self._on_list_key_press
        
        help_lbl = QLabel("Drag items to reorder. Select and press Delete to remove.")
        help_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(help_lbl)
        layout.addWidget(self.list_widget)

    def _on_list_key_press(self, event):
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            for item in self.list_widget.selectedItems():
                self.list_widget.takeItem(self.list_widget.row(item))
            self._update_merge_btn()
        else:
            QListWidget.keyPressEvent(self.list_widget, event)

    def _on_browse(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF Files (*.pdf);;All Files (*)")
        if files: self._on_files_added(files)

    def _on_files_added(self, files):
        for f in files:
            if f.lower().endswith('.pdf'):
                item = QListWidgetItem(os.path.basename(f))
                item.setData(Qt.UserRole, f)
                self.list_widget.addItem(item)
        self._update_merge_btn()

    def _update_merge_btn(self):
        self.merge_btn.setEnabled(self.list_widget.count() > 1)

    def _on_merge(self):
        if self.list_widget.count() < 2: return
        out_path, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", "merged.pdf", "PDF Files (*.pdf)")
        if not out_path: return
            
        input_paths = [self.list_widget.item(i).data(Qt.UserRole) for i in range(self.list_widget.count())]
            
        progress = QProgressDialog("Merging PDFs...", None, 0, 0, self)
        progress.setWindowTitle("Merging")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        
        try:
            merge_pdfs(input_paths, out_path)
            success = True
            err_msg = ""
        except Exception as e:
            success, err_msg = False, str(e)
            
        progress.close()
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Merge Complete")
        if success:
            msg_box.setText(f"<span style='color: {SUCCESS}; font-weight: bold;'>[✓]</span> Merged {len(input_paths)} files into:<br>{os.path.basename(out_path)}")
        else:
            msg_box.setText(f"<span style='color: {ERROR}; font-weight: bold;'>[✕]</span> Merge failed:<br>{err_msg}")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.exec()

class OrganizePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tool_configs = [
            ("merge", "Merge"),
            ("split", "Split"),
            ("extract", "Extract Pages"),
            ("delete", "Delete Pages"),
            ("reorder", "Reorder Pages"),
            ("rotate", "Rotate Pages")
        ]
        self.current_tool_id = None
        self._setup_ui()
        
        # Select first tool by default
        if self.tool_configs:
            self._on_tool_selected(self.tool_configs[0][0])
            
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        title = QLabel("Organize")
        title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 18px; font-weight: 500;")
        layout.addWidget(title)
        
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.cards = {}
        for t_id, title_text in self.tool_configs:
            card = ToolCard(t_id, title_text, "organize")
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
        
        # Tool-specific controls area (placeholders)
        self.tool_controls_stack = QStackedWidget()
        self.tool_controls_stack.setStyleSheet("background: transparent;")
        layout.addWidget(self.tool_controls_stack)
        
        self.tool_placeholders = {}
        for t_id, title_text in self.tool_configs:
            if t_id == "merge":
                ph = MergeToolWidget()
            elif t_id == "split":
                ph = SplitToolWidget()
            elif t_id == "extract":
                ph = ThumbnailActionToolWidget("Extract Pages", extract_pages, mode="select")
            elif t_id == "delete":
                ph = ThumbnailActionToolWidget("Delete Pages", delete_pages, mode="select")
            elif t_id == "reorder":
                ph = ThumbnailActionToolWidget("Reorder Pages", reorder_pages, mode="reorder")
            elif t_id == "rotate":
                ph = ThumbnailActionToolWidget("Rotate Pages", rotate_pages, mode="rotate")
            else:
                ph = QWidget()
                ph_layout = QVBoxLayout(ph)
                ph_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                lbl = QLabel(f"[{title_text} controls will go here]")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px;")
                
                ph_layout.addWidget(lbl)
            
            self.tool_controls_stack.addWidget(ph)
            self.tool_placeholders[t_id] = ph
            
        layout.addStretch()
        
    def _on_tool_selected(self, tool_id: str):
        self.current_tool_id = tool_id
        for tid, card in self.cards.items():
            card.setChecked(tid == tool_id)
            
        if tool_id in self.tool_placeholders:
            self.tool_controls_stack.setCurrentWidget(self.tool_placeholders[tool_id])
