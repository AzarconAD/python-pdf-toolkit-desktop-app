from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

class DropZone(QWidget):
    """
    Widget that accepts drag-and-drop files and provides a 'Browse' button.
    """
    files_dropped = Signal(list)
    browse_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAcceptDrops(True)
        
        from gui.styles.theme import ACCENT, SURFACE, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ON_ACCENT
        from gui.utils.icons import get_icon
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(get_icon("cloud-upload", ACCENT, 32).pixmap(32, 32))
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("border: none; background: transparent;")
        
        self.label_main = QLabel("Drag & drop files here")
        self.label_main.setAlignment(Qt.AlignCenter)
        self.label_main.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 500; border: none; background: transparent;")
        
        self.label_sub = QLabel("or")
        self.label_sub.setAlignment(Qt.AlignCenter)
        self.label_sub.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; border: none; background: transparent;")
        
        self.browse_btn = QPushButton("Browse files")
        self.browse_btn.setObjectName("BrowseBtn")
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setFixedWidth(120)
        self.browse_btn.setStyleSheet(f"""
            #BrowseBtn {{
                background-color: {ACCENT};
                color: {TEXT_ON_ACCENT};
                border: 1px solid {ACCENT};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            #BrowseBtn:hover {{
                opacity: 0.9;
                background-color: #3A7CE0;
            }}
        """)
        self.browse_btn.clicked.connect(self.browse_clicked.emit)
        
        self.set_compact(False)
        
    def set_compact(self, is_compact: bool):
        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
        from gui.styles.theme import TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, SURFACE, BORDER
        
        old_layout = self.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            QWidget().setLayout(old_layout)
            
        self._is_compact = is_compact
        if is_compact:
            self.setMinimumHeight(60)
            self.setMaximumHeight(60)
            self.setFixedWidth(16777215)
            self.setMinimumWidth(0)
            
            self.setStyleSheet(f"""
                #DropZone {{
                    border: 2px dashed {BORDER};
                    border-radius: 8px;
                    background-color: {SURFACE};
                }}
            """)
            
            h_layout = QHBoxLayout(self)
            h_layout.setAlignment(Qt.AlignCenter)
            
            self.label_main.setText("Drag & Drop files here or")
            self.label_main.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; font-weight: bold; border: none; background: transparent;")
            
            self.icon_lbl.hide()
            self.label_sub.hide()
            
            h_layout.addWidget(self.label_main)
            h_layout.addWidget(self.browse_btn)
        else:
            self.setMinimumHeight(250)
            self.setMaximumHeight(16777215)
            self.setFixedWidth(420)
            
            self.setStyleSheet(f"""
                #DropZone {{
                    border: 2px dashed {ACCENT};
                    border-radius: 12px;
                    background-color: {SURFACE};
                }}
            """)
            
            v_layout = QVBoxLayout(self)
            v_layout.setAlignment(Qt.AlignCenter)
            v_layout.setContentsMargins(40, 40, 40, 40)
            
            self.label_main.setText("Drag & drop files here")
            self.label_main.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 500; border: none; background: transparent;")
            
            self.icon_lbl.show()
            self.label_sub.show()
            
            v_layout.addWidget(self.icon_lbl, alignment=Qt.AlignHCenter)
            v_layout.addSpacing(10)
            v_layout.addWidget(self.label_main, alignment=Qt.AlignHCenter)
            v_layout.addSpacing(5)
            v_layout.addWidget(self.label_sub, alignment=Qt.AlignHCenter)
            v_layout.addSpacing(15)
            v_layout.addWidget(self.browse_btn, alignment=Qt.AlignHCenter)
            
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            from gui.styles.theme import ACCENT, SURFACE_ELEVATED
            self.setStyleSheet(f"""
                #DropZone {{
                    border: 2px dashed {ACCENT};
                    border-radius: 12px;
                    background-color: {SURFACE_ELEVATED};
                }}
            """)
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        self.set_compact(getattr(self, '_is_compact', False))
        
    def dropEvent(self, event):
        self.dragLeaveEvent(event)
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if files:
            self.files_dropped.emit(files)
