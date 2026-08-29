from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Toolbox")
        self.resize(1000, 700)
        
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(central_widget)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("QStackedWidget { background-color: transparent; }")
        main_layout.addWidget(self.stacked_widget, stretch=1)
        
        self._setup_pages()
        
    def _setup_pages(self):
        from gui.pages.workspace_page import UnifiedWorkspacePage
        
        self.workspace_page = UnifiedWorkspacePage()
        self.workspace_page.tool_selected.connect(lambda t: print(f"DEBUG: tool_selected signal fired with id: {t}"))
        self.stacked_widget.addWidget(self.workspace_page)
