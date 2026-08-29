import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.styles.theme import get_stylesheet

def main():
    """Bootstrap the PySide6 application."""
    print("PDF Toolbox GUI starting...")
    # Initialize the application
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Toolbox")
    
    # Apply global stylesheet
    app.setStyleSheet(get_stylesheet())
    app.setApplicationDisplayName("PDF Toolbox")
    
    # Instantiate and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
