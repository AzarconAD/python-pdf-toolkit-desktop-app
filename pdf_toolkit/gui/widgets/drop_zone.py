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
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAcceptDrops(True)
        
        from gui.styles.theme import BORDER, ACCENT, TEXT_SECONDARY, SURFACE, SURFACE_ELEVATED
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.label = QLabel("Drag & Drop files here\nor")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; font-weight: bold; background: transparent;")
        
        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setFixedWidth(120)
        # Relying on global stylesheet for base button styling
        self.browse_btn.clicked.connect(self.browse_clicked.emit)
        
        layout.addWidget(self.label)
        layout.addWidget(self.browse_btn, alignment=Qt.AlignHCenter)
        
        # Base styling
        self.setStyleSheet(f"""
            DropZone {{
                border: 2px dashed {BORDER};
                border-radius: 8px;
                background-color: {SURFACE};
            }}
        """)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            from gui.styles.theme import ACCENT, SURFACE_ELEVATED
            self.setStyleSheet(f"""
                DropZone {{
                    border: 2px dashed {ACCENT};
                    border-radius: 8px;
                    background-color: {SURFACE_ELEVATED};
                }}
            """)
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        from gui.styles.theme import BORDER, SURFACE
        self.setStyleSheet(f"""
            DropZone {{
                border: 2px dashed {BORDER};
                border-radius: 8px;
                background-color: {SURFACE};
            }}
        """)
        
    def dropEvent(self, event):
        self.dragLeaveEvent(event)  # Reset visual state
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if files:
            self.files_dropped.emit(files)
