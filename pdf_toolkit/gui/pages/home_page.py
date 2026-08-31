from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal
from gui.styles.theme import SURFACE_ELEVATED, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, BG_PAGE, BORDER, SURFACE
from gui.utils.icons import get_icon
_TOOLS = {
    "Convert": {
        "enabled": True,
        "items": [
            ("word",         "PDF to Word",    "pdf_to_docx",    False),
            ("excel",        "PDF to Excel",   "pdf_to_xlsx",    False),
            ("ppt",          "PDF to PPT",     "pdf_to_pptx",    False),
            ("image",        "PDF to Images",  "pdf_to_images",  False),
            ("---",          "",               None,             True),
            ("word",         "Word to PDF",    "docx_to_pdf",    False),
            ("excel",        "Excel to PDF",   "xlsx_to_pdf",    False),
            ("ppt",          "PPT to PDF",     "pptx_to_pdf",    False),
            ("image",        "Images to PDF",  "images_to_pdf",  False),
        ],
    },
    "Organize": {
        "enabled": True,
        "items": [
            ("merge",        "Merge",          "merge",          False),
            ("split",        "Split",          "split",          False),
            ("extract",      "Extract Pages",  "extract",        False),
            ("delete-pages", "Delete Pages",   "delete",         False),
            ("reorder",      "Reorder Pages",  "reorder",        False),
            ("rotate",       "Rotate Pages",   "rotate",         False),
        ],
    },
    "Optimize": {
        "enabled": True,
        "items": [
            ("optimize",     "Compress PDF",   "compress",       False),
        ],
    },
    "Edit": {
        "enabled": True,
        "items": [
            ("edit",         "Edit PDF",       "edit_pdf",       False),
        ],
    },
    "Security": {
        "enabled": True,
        "items": [
            ("security",     "Protect PDF",      "protect",      False),
            ("security",     "Unlock PDF",       "unlock",       False),
            ("security",     "Watermark",        "watermark",    False),
            ("security",     "Add Page Numbers", "page_numbers", False),
        ],
    },
}
from gui.widgets.tool_card import ToolCard

class NavTab(QFrame):
    def __init__(self, cat_id: str, icon_name: str, text: str, is_active: bool = False, on_click=None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.cat_id = cat_id
        self._on_click = on_click
        self.icon_name = icon_name
        self.text = text
        
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(16, 0, 16, 0)
        self._layout.setSpacing(8)
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setStyleSheet("border: none; background: transparent;")
        
        self.text_lbl = QLabel(text)
        
        self._layout.addWidget(self.icon_lbl)
        self._layout.addWidget(self.text_lbl)
        
        self.set_active(is_active)
        
    def set_active(self, is_active: bool):
        color = ACCENT if is_active else TEXT_SECONDARY
        text_color = TEXT_PRIMARY if is_active else TEXT_SECONDARY
        
        self.icon_lbl.setPixmap(get_icon(self.icon_name, color, 18).pixmap(18, 18))
        
        weight = "600" if is_active else "500"
        self.text_lbl.setStyleSheet(f"color: {text_color}; font-size: 14px; font-weight: {weight}; border: none; background: transparent;")
        
        bg_color = SURFACE_ELEVATED if is_active else "transparent"
        self.setStyleSheet(f"""
            NavTab {{
                background-color: {bg_color};
                border-radius: 20px;
            }}
            NavTab:hover {{
                background-color: {SURFACE_ELEVATED};
            }}
        """)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self._on_click:
            self._on_click(self.cat_id)

class HomePage(QWidget):
    tool_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"HomePage {{ background-color: {BG_PAGE}; }}")
        
        self._active_cat = "Convert"
        self._tabs = {}
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Main Content Container ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(30)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        main_layout.addWidget(content_widget)
        
        # Titles Container
        titles_layout = QVBoxLayout()
        titles_layout.setSpacing(12)
        titles_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        from PySide6.QtGui import QPixmap
        from pathlib import Path
        
        # Logo
        logo_lbl = QLabel()
        logo_path = str(Path(__file__).parent.parent.parent / "assets" / "app_icon.png")
        pixmap = QPixmap(logo_path).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        logo_lbl.setPixmap(pixmap)
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setStyleSheet("border: none; background: transparent;")
        titles_layout.addWidget(logo_lbl)
        
        # Hero Title
        hero_title = QLabel("PDF ToolBox")
        hero_title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 36px; font-weight: bold; border: none; background: transparent;")
        hero_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titles_layout.addWidget(hero_title)
        
        # Subtitle
        title_lbl = QLabel("What would you like to do?")
        title_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 18px; font-weight: 500; border: none; background: transparent;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titles_layout.addWidget(title_lbl)
        
        content_layout.addStretch()
        content_layout.addLayout(titles_layout)
        
        # Navbar
        navbar = QHBoxLayout()
        navbar.setSpacing(8)
        navbar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        categories = ["Convert", "Organize", "Optimize", "Edit", "Security"]
        for cat in categories:
            is_active = (cat == self._active_cat)
            tab = NavTab(cat, cat.lower(), cat, is_active, on_click=self._switch_category)
            self._tabs[cat] = tab
            navbar.addWidget(tab)
            
        content_layout.addLayout(navbar)
        
        # Tool Grid
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addLayout(self.grid_layout)
        
        self._populate_grid(self._active_cat)
        
        content_layout.addStretch()

    def _switch_category(self, cat: str):
        if cat == self._active_cat:
            return
        
        self._tabs[self._active_cat].set_active(False)
        self._active_cat = cat
        self._tabs[cat].set_active(True)
        
        self._populate_grid(cat)

    def _populate_grid(self, cat: str):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        cat_data = _TOOLS[cat]
        enabled = cat_data["enabled"]
        
        row, col = 0, 0
        max_cols = 4
        
        for icon_name, label, tool_id, is_divider in cat_data["items"]:
            if is_divider:
                continue
            card = ToolCard(
                tool_id=tool_id, 
                icon_name=icon_name, 
                label_text=label, 
                enabled=enabled,
                on_click=self.tool_selected.emit
            )
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

