from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from gui.widgets.sidebar import Sidebar
from gui.pages.home_page import HomePage
from gui.pages.convert_tool_page import ConvertToolPage

# Core imports for tool configuration
from core.convert_to import pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, pdf_to_images
from core.convert_from import docx_to_pdf, xlsx_to_pdf, pptx_to_pdf, images_to_pdf

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Toolkit")
        self.resize(1000, 700)
        
        # Main Layout Setup
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(central_widget)
        
        # 1. Sidebar (Left)
        self.sidebar = Sidebar()
        self.sidebar.category_selected.connect(self._on_sidebar_category)
        main_layout.addWidget(self.sidebar)
        
        # 2. Stacked Widget (Right)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("QStackedWidget { background-color: #ffffff; }")
        main_layout.addWidget(self.stacked_widget, stretch=1)
        
        # Setup Pages
        self._setup_pages()
        
    def _setup_pages(self):
        # Instantiate and add Home Page (Grid of tools)
        self.home_page = HomePage()
        self.home_page.tool_selected.connect(self._on_tool_selected)
        self.stacked_widget.addWidget(self.home_page)
        
        self.tool_pages = {}
        
        # Configuration for all 8 Phase 1 Convert tools
        tool_configs = [
            ("pdf_to_docx", "PDF to Word", ['.pdf'], pdf_to_docx, "independent"),
            ("pdf_to_xlsx", "PDF to Excel", ['.pdf'], pdf_to_xlsx, "independent"),
            ("pdf_to_pptx", "PDF to PowerPoint", ['.pdf'], pdf_to_pptx, "independent"),
            ("pdf_to_images", "PDF to Images", ['.pdf'], pdf_to_images, "independent"),
            ("docx_to_pdf", "Word to PDF", ['.docx'], docx_to_pdf, "independent"),
            ("xlsx_to_pdf", "Excel to PDF", ['.xlsx'], xlsx_to_pdf, "independent"),
            ("pptx_to_pdf", "PowerPoint to PDF", ['.pptx'], pptx_to_pdf, "independent"),
            ("images_to_pdf", "Images to PDF", ['.jpg', '.jpeg', '.png'], images_to_pdf, "combine")
        ]
        
        # Instantiate all 8 ConvertToolPages
        for t_id, title, exts, func, mode in tool_configs:
            page = ConvertToolPage(title, exts, func, mode)
            page.back_clicked.connect(self._show_home_page)
            self.stacked_widget.addWidget(page)
            self.tool_pages[t_id] = page
            
    def _on_sidebar_category(self, category: str):
        # Currently only Convert is active, so any click defaults to HomePage logic
        if category == "Convert":
            self._show_home_page()
            
    def _on_tool_selected(self, tool_id: str):
        # Switch to the specific configured tool page
        if tool_id in self.tool_pages:
            self.stacked_widget.setCurrentWidget(self.tool_pages[tool_id])
            
    def _show_home_page(self):
        self.stacked_widget.setCurrentWidget(self.home_page)
