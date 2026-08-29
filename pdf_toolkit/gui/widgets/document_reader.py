from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from gui.utils.thumbnails import render_page_thumbnail, get_page_count
from gui.styles import theme

class ResponsiveImageLabel(QLabel):
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._original_pixmap = pixmap
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 1px solid " + theme.BORDER + "; background: " + theme.SURFACE_ELEVATED + ";")
        self.setMinimumSize(50, 50)
        from PySide6.QtWidgets import QSizePolicy
        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        self._update_pixmap()

    def hasHeightForWidth(self):
        return True
        
    def heightForWidth(self, width):
        if self._original_pixmap.isNull() or self._original_pixmap.width() == 0:
            return 50
        ratio = self._original_pixmap.height() / self._original_pixmap.width()
        target_width = min(width, self._original_pixmap.width())
        return int(target_width * ratio)

    def sizeHint(self):
        if self._original_pixmap.isNull():
            return super().sizeHint()
        w = self._original_pixmap.width()
        from PySide6.QtCore import QSize
        return QSize(w, self.heightForWidth(w))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()
        
    def _update_pixmap(self):
        if self._original_pixmap.isNull():
            return
            
        avail_width = self.width()
        orig_width = self._original_pixmap.width()
        
        target_width = min(avail_width, orig_width)
        
        if target_width > 0:
            scaled = self._original_pixmap.scaledToWidth(
                target_width, Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled)

class DocumentReader(QWidget):
    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self._setup_ui()
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(24)
        
        try:
            total_pages = get_page_count(self.pdf_path)
        except Exception:
            err = QLabel("Failed to load document")
            err.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
            main_layout.addWidget(err)
            return
            
        for i in range(total_pages):
            page_num = i + 1
            
            page_container = QWidget()
            page_layout = QVBoxLayout(page_container)
            page_layout.setContentsMargins(0, 0, 0, 0)
            page_layout.setSpacing(8)
            page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            try:
                pixmap = render_page_thumbnail(self.pdf_path, page_num, max_size=900)
                img_lbl = ResponsiveImageLabel(pixmap)
                page_layout.addWidget(img_lbl, 1)
            except Exception:
                err = QLabel(f"Failed to render page {page_num}")
                err.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
                page_layout.addWidget(err)
                
            text_label = QLabel(f"Page {page_num}")
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: 12px; font-weight: 500; border: none;")
            page_layout.addWidget(text_label, 0, Qt.AlignmentFlag.AlignHCenter)
            
            main_layout.addWidget(page_container)
