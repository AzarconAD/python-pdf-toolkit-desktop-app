from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QStackedWidget, QMessageBox, QGridLayout)
from PySide6.QtCore import Qt, Signal
import os

from gui.styles.theme import BG_PAGE, SURFACE_ELEVATED
from gui.widgets.edit_canvas import EditCanvas

class EditPage(QWidget):
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG_PAGE};")
        
        self.canvas = None
        self.canvas_wrapper = None
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Header
        self.header = QWidget()
        self.header.setStyleSheet(f"background-color: {SURFACE_ELEVATED}; border-bottom: 1px solid #33353C;")
        self.header.setFixedHeight(60)
        header_layout = QGridLayout(self.header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        self.back_btn = QPushButton("← Back")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #EAEAEC;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #4C8DFF;
            }
        """)
        self.back_btn.clicked.connect(self._on_back)
        
        from gui.utils.icons import get_icon
        from gui.styles.theme import TEXT_SECONDARY
        
        self.title_lbl = QLabel("Edit PDF")
        self.title_lbl.setStyleSheet("color: #EAEAEC; font-size: 15px; font-weight: bold; border: none;")
        
        self.active_tool_lbl = QLabel("Active tool: None")
        self.active_tool_lbl.setStyleSheet("""
            QLabel {
                background-color: #24262C;
                color: #9497A0;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #33353C;
                border-radius: 12px;
                padding: 4px 12px;
            }
        """)
        self.active_tool_lbl.hide()
        
        self.save_btn = QPushButton("Save Output...")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4C8DFF;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3b7ced;
            }
        """)
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.hide()
        
        self.page_nav_container = QWidget()
        page_nav_layout = QHBoxLayout(self.page_nav_container)
        page_nav_layout.setContentsMargins(0, 0, 0, 0)
        page_nav_layout.setSpacing(10)
        
        btn_style = """
            QPushButton { background: #24262C; border: 1px solid #33353C; border-radius: 4px; }
            QPushButton:hover { border: 1px solid #4C8DFF; background: #2D3038; }
            QPushButton:disabled { border: 1px solid #33353C; background: #1B1D22; }
        """
        
        self.prev_page_btn = QPushButton()
        self.prev_page_btn.setIcon(get_icon("chevron-left", TEXT_SECONDARY, 18))
        self.prev_page_btn.setFixedSize(28, 28)
        self.prev_page_btn.setStyleSheet(btn_style)
        self.prev_page_btn.clicked.connect(self._prev_page)
        
        self.next_page_btn = QPushButton()
        self.next_page_btn.setIcon(get_icon("chevron-right", TEXT_SECONDARY, 18))
        self.next_page_btn.setFixedSize(28, 28)
        self.next_page_btn.setStyleSheet(btn_style)
        self.next_page_btn.clicked.connect(self._next_page)
        
        self.page_lbl = QLabel("Page - of -")
        self.page_lbl.setStyleSheet("color: #9497A0; font-size: 13px; font-weight: bold; border: none;")
        
        page_nav_layout.addWidget(self.prev_page_btn)
        page_nav_layout.addWidget(self.page_lbl)
        page_nav_layout.addWidget(self.next_page_btn)
        
        self.page_nav_container.hide()
        
        # Left section
        left_layout = QHBoxLayout()
        left_layout.setSpacing(16)
        left_layout.addWidget(self.back_btn)
        left_layout.addWidget(self.title_lbl)
        
        # Right section
        right_layout = QHBoxLayout()
        right_layout.setSpacing(12)
        right_layout.addWidget(self.active_tool_lbl)
        right_layout.addWidget(self.save_btn)
        
        header_layout.addLayout(left_layout, 0, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.page_nav_container, 0, 1, Qt.AlignmentFlag.AlignCenter)
        header_layout.addLayout(right_layout, 0, 2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        header_layout.setColumnStretch(0, 1)
        header_layout.setColumnStretch(1, 0)
        header_layout.setColumnStretch(2, 1)
        
        self.layout.addWidget(self.header)
        
        # Stack for Empty State vs Canvas
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack, stretch=1)
        
        # Empty State
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.select_btn = QPushButton("Select PDF to Edit")
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #4C8DFF;
                color: white;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3b7ced;
            }
        """)
        self.select_btn.clicked.connect(self._select_file)
        empty_layout.addWidget(self.select_btn)
        
        self.stack.addWidget(self.empty_state)
        
    def _select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF to Edit", "", "PDF Files (*.pdf)")
        if file_path:
            self.load_pdf(file_path)
            
    def load_pdf(self, file_path: str):
        if self.canvas_wrapper:
            self.canvas.cleanup()
            self.stack.removeWidget(self.canvas_wrapper)
            self.canvas_wrapper.deleteLater()
            
        self.canvas = EditCanvas(file_path)
        self.title_lbl.setText(f"Editing: {os.path.basename(file_path)}")
        self.active_tool_lbl.show()
        
        self.canvas_wrapper = QWidget()
        wrapper_layout = QHBoxLayout(self.canvas_wrapper)
        wrapper_layout.setContentsMargins(0,0,0,0)
        wrapper_layout.setSpacing(0)
        
        wrapper_layout.addWidget(self.canvas.left_rail)
        
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setSpacing(0)
        
        right_layout.addWidget(self.canvas.top_strip)
        right_layout.addWidget(self.canvas)
        
        wrapper_layout.addWidget(right_container)
        
        self.stack.addWidget(self.canvas_wrapper)
        self.stack.setCurrentWidget(self.canvas_wrapper)
        self.save_btn.show()
        
        self.canvas.page_changed.connect(self._on_page_changed)
        self.canvas.active_tool_changed.connect(self._on_active_tool_changed)
        self.page_nav_container.show()
        
        # Manually trigger first update
        self._on_page_changed(self.canvas.current_page, self.canvas.page_count)
        
    def _on_active_tool_changed(self, tool_name: str):
        self.active_tool_lbl.setText(f"Active tool: {tool_name}")
        
    def _on_page_changed(self, current_page: int, total_pages: int):
        self.page_lbl.setText(f"Page {current_page + 1} of {total_pages}")
        self.prev_page_btn.setEnabled(current_page > 0)
        self.next_page_btn.setEnabled(current_page < total_pages - 1)
        
    def _prev_page(self):
        if self.canvas and self.canvas.current_page > 0:
            self.canvas.load_page(self.canvas.current_page - 1)
            
    def _next_page(self):
        if self.canvas and self.canvas.current_page < self.canvas.page_count - 1:
            self.canvas.load_page(self.canvas.current_page + 1)
        
    def _on_back(self):
        if self.canvas_wrapper:
            self.canvas.cleanup()
            self.stack.removeWidget(self.canvas_wrapper)
            self.canvas_wrapper.deleteLater()
            self.canvas = None
            self.canvas_wrapper = None
            self.stack.setCurrentWidget(self.empty_state)
            self.save_btn.hide()
            self.page_nav_container.hide()
        self.back_requested.emit()
        
    def _on_save(self):
        if not self.canvas:
            return
            
        out_path, _ = QFileDialog.getSaveFileName(self, "Save Edited PDF", "", "PDF Files (*.pdf)")
        if not out_path:
            return
            
        elements = self.canvas.get_elements()
        working_path = self.canvas.working_pdf_path
        
        from core.edit import apply_edits
        try:
            apply_edits(working_path, out_path, elements)
            QMessageBox.information(self, "Success", "PDF saved successfully!")
            self._on_back()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save PDF:\n{e}")
