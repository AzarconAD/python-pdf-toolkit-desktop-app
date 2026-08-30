from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from gui.styles.theme import SURFACE, SURFACE_ELEVATED, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT
from gui.utils.icons import get_icon

class ToolCard(QFrame):
    def __init__(self, tool_id: str, icon_name: str, label_text: str, enabled: bool = True, on_click=None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedSize(140, 110)
        self.tool_id = tool_id
        self._on_click = on_click
        self._enabled = enabled
        
        if enabled:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        
        icon_color = ACCENT if enabled else TEXT_SECONDARY
        text_color = TEXT_PRIMARY if enabled else TEXT_SECONDARY
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(get_icon(icon_name, icon_color, 32).pixmap(32, 32))
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("border: none; background: transparent;")
        
        self.text_lbl = QLabel(label_text)
        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_lbl.setStyleSheet(f"color: {text_color}; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        self.text_lbl.setWordWrap(True)
        
        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.text_lbl)
        
        hover_style = f"""
            ToolCard:hover {{
                background-color: {SURFACE_ELEVATED};
                border: 1px solid {ACCENT};
            }}
        """ if enabled else ""
        
        self.setStyleSheet(f"""
            ToolCard {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            {hover_style}
        """)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self._enabled and self._on_click and event.button() == Qt.MouseButton.LeftButton:
            self._on_click(self.tool_id)
