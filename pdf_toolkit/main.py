import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    """Bootstrap the PySide6 application."""
    print("PDF Toolkit GUI starting...")
    # Initialize the application
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Toolkit")
    app.setApplicationDisplayName("PDF Toolkit")
    
    # Instantiate and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
