import sys

# Silence the fitz deprecation warning that pdf2docx triggers at import time.
# The warning is a Python-level print to pymupdf._g_out_message (a cached stdout ref).
# We null that ref out BEFORE importing fitz so the print() call is a no-op.
import pymupdf as _pymupdf  # safe: importing pymupdf itself does NOT print the warning
_saved_msg = _pymupdf._g_out_message
_pymupdf._g_out_message = None
import fitz  # triggers the warning call, which now writes to None and is silently dropped
_pymupdf._g_out_message = _saved_msg
del _pymupdf, _saved_msg
import logging
logging.getLogger("pikepdf").setLevel(logging.WARNING)

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.styles.theme import get_stylesheet

def main():
    """Bootstrap the PySide6 application."""
    print("PDF ToolBox GUI starting...")
    app = QApplication(sys.argv)
    app.setApplicationName("PDF ToolBox")
    
    from PySide6.QtGui import QIcon
    import os
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "app_icon.png")
    app.setWindowIcon(QIcon(icon_path))
    
    from PySide6.QtGui import QFont
    app.setFont(QFont("Segoe UI", 10))
    
    app.setStyleSheet(get_stylesheet())
    app.setApplicationDisplayName("PDF ToolBox")
    
    window = MainWindow()
    window.showMaximized()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
