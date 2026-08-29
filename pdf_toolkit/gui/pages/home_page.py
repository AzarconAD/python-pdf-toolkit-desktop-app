from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

class ToolCard(QPushButton):
    """
    A custom clickable card widget for a specific tool.
    Inherits from QPushButton to leverage built-in pressed/hover states.
    """
    def __init__(self, tool_id, title, description, parent=None):
        super().__init__(parent)
        self.tool_id = tool_id
        
        layout = QVBoxLayout(self)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-weight: bold; font-size: 16px; border: none; background: transparent;")
        
        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("color: #666; font-size: 12px; border: none; background: transparent;")
        desc_lbl.setWordWrap(True)
        
        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)
        
        self.setFixedSize(200, 120)
        self.setCursor(Qt.PointingHandCursor)
        
        # Style the QPushButton to look like a modern card
        self.setStyleSheet("""
            ToolCard {
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                background-color: #ffffff;
                text-align: left;
            }
            ToolCard:hover {
                border: 1px solid #0078D7;
                background-color: #f3f9ff;
            }
            ToolCard:pressed {
                background-color: #e5f0fa;
            }
        """)

class HomePage(QWidget):
    """
    The main overview page showing the grid of Convert tools.
    Emits tool_selected(str) when a tool card is clicked.
    """
    tool_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        title = QLabel("Convert PDF")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title)
        
        grid = QGridLayout()
        grid.setSpacing(20)
        
        tools = [
            ("pdf_to_docx", "PDF to Word", "Convert PDF to editable DOCX document"),
            ("pdf_to_xlsx", "PDF to Excel", "Convert PDF to XLSX spreadsheet"),
            ("pdf_to_pptx", "PDF to PowerPoint", "Convert PDF to PPTX presentation"),
            ("pdf_to_images", "PDF to Images", "Extract PDF pages to JPG or PNG"),
            ("docx_to_pdf", "Word to PDF", "Convert Word DOCX to PDF format"),
            ("xlsx_to_pdf", "Excel to PDF", "Convert Excel XLSX to PDF format"),
            ("pptx_to_pdf", "PowerPoint to PDF", "Convert PowerPoint PPTX to PDF format"),
            ("images_to_pdf", "Images to PDF", "Combine JPG or PNG into a single PDF")
        ]
        
        row, col = 0, 0
        for tool_id, title_text, desc_text in tools:
            card = ToolCard(tool_id, title_text, desc_text)
            # Ensure the specific tool_id is captured in the closure
            card.clicked.connect(lambda checked=False, tid=tool_id: self.tool_selected.emit(tid))
            grid.addWidget(card, row, col)
            
            # Layout as 4 columns
            col += 1
            if col > 3:
                col = 0
                row += 1
                
        main_layout.addLayout(grid)
        main_layout.addStretch()  # Push the grid to the top
