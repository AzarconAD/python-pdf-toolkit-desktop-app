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
        self.setAcceptDrops(True)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.label = QLabel("Drag & Drop files here\nor")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #666; font-size: 14px; font-weight: bold; background: transparent;")
        
        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setFixedWidth(120)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0; border: 1px solid #ccc;
                border-radius: 4px; padding: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #e4e4e4; }
        """)
        self.browse_btn.clicked.connect(self.browse_clicked.emit)
        
        layout.addWidget(self.label)
        layout.addWidget(self.browse_btn, alignment=Qt.AlignHCenter)
        
        # Base styling
        self.setStyleSheet("""
            DropZone {
                border: 2px dashed #b0b0b0;
                border-radius: 8px;
                background-color: #fafafa;
            }
        """)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet("""
                DropZone {
                    border: 2px dashed #0078D7;
                    border-radius: 8px;
                    background-color: #e5f0fa;
                }
            """)
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            DropZone {
                border: 2px dashed #b0b0b0;
                border-radius: 8px;
                background-color: #fafafa;
            }
        """)
        
    def dropEvent(self, event):
        self.dragLeaveEvent(event)  # Reset visual state
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if files:
            self.files_dropped.emit(files)
