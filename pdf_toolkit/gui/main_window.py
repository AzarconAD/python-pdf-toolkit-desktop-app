from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from gui.widgets.sidebar import Sidebar
from core.convert_to import pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, pdf_to_images
from core.convert_from import docx_to_pdf, xlsx_to_pdf, pptx_to_pdf, images_to_pdf

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
        
        self.sidebar = Sidebar()
        self.sidebar.category_selected.connect(self._on_sidebar_category)
        main_layout.addWidget(self.sidebar)
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("QStackedWidget { background-color: transparent; }")
        main_layout.addWidget(self.stacked_widget, stretch=1)
        
        self._setup_pages()
        
    def _setup_pages(self):
        from gui.pages.convert_page import UnifiedConvertPage
        
        tool_configs = [
            ("pdf_to_docx", "PDF to Word", ['.pdf'], pdf_to_docx, "independent"),
            ("pdf_to_xlsx", "PDF to Excel", ['.pdf'], pdf_to_xlsx, "independent"),
            ("pdf_to_pptx", "PDF to PPT", ['.pdf'], pdf_to_pptx, "independent"),
            ("pdf_to_images", "PDF to Images", ['.pdf'], pdf_to_images, "independent"),
            ("docx_to_pdf", "Word to PDF", ['.docx'], docx_to_pdf, "independent"),
            ("xlsx_to_pdf", "Excel to PDF", ['.xlsx'], xlsx_to_pdf, "independent"),
            ("pptx_to_pdf", "PPT to PDF", ['.pptx'], pptx_to_pdf, "independent"),
            ("images_to_pdf", "Images to PDF", ['.jpg', '.jpeg', '.png'], images_to_pdf, "combine")
        ]
        
        self.convert_page = UnifiedConvertPage(tool_configs)
        self.stacked_widget.addWidget(self.convert_page)
            
    def _on_sidebar_category(self, category: str):
        if category == "Convert":
            self.stacked_widget.setCurrentWidget(self.convert_page)
