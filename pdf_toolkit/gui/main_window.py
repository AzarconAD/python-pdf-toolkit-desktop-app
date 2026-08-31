from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF ToolBox")
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
        from gui.pages.home_page import HomePage
        from gui.pages.edit_page import EditPage
        
        self.home_page = HomePage()
        self.workspace_page = UnifiedWorkspacePage()
        self.edit_page = EditPage()
        
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.workspace_page)
        self.stacked_widget.addWidget(self.edit_page)
        
        self.home_page.tool_selected.connect(self._on_home_tool_selected)
        self.workspace_page.back_requested.connect(self._on_workspace_back)
        self.edit_page.back_requested.connect(self._on_edit_back)
        
    def _on_workspace_back(self):
        # Reset workspace state
        self.workspace_page._reset_to_state1()
        # Switch back to home
        self.stacked_widget.setCurrentWidget(self.home_page)
        
    def _on_edit_back(self):
        self.stacked_widget.setCurrentWidget(self.home_page)
        
    def _on_home_tool_selected(self, tool_id: str):
        if tool_id == "edit_pdf":
            self.stacked_widget.setCurrentWidget(self.edit_page)
            return
            
        # Switch to workspace page
        self.stacked_widget.setCurrentWidget(self.workspace_page)
        # Inform workspace page of the selected tool
        self.workspace_page.tool_selected.emit(tool_id)
        self.workspace_page._on_tool_selected(tool_id)
        
    def closeEvent(self, event):
        if hasattr(self, 'edit_page') and self.edit_page.canvas:
            self.edit_page.canvas.cleanup()
        super().closeEvent(event)
