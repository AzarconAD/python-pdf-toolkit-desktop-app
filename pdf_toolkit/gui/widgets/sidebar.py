from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QLabel

class Sidebar(QWidget):
    """
    Sidebar navigation widget.
    Emits category_selected(str) when a category is clicked.
    """
    category_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(10)

        # Define categories: (Name, is_enabled, tooltip, icon_name)
        categories = [
            ("Convert", True, "Convert between PDF and other formats", "convert"),
            ("Organize", False, "Coming soon", "organize"),
            ("Optimize", False, "Coming soon", "optimize"),
            ("Edit", False, "Coming soon", "edit"),
            ("Security", False, "Coming soon", "security"),
        ]
        
        self.buttons = {}

        from gui.styles.theme import ACCENT, TEXT_SECONDARY, TEXT_PRIMARY, SURFACE_ELEVATED
        from gui.utils.icons import get_icon

        # Add Title
        title_lbl = QLabel("PDF Toolbox")
        title_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 24px; font-weight: 800; padding: 10px 15px; margin-bottom: 10px;")
        layout.addWidget(title_lbl)

        for name, is_enabled, tooltip, icon_name in categories:
            btn = QPushButton(name)
            btn.setToolTip(tooltip)
            
            if is_enabled:
                # Active/Enabled item styling
                btn.setIcon(get_icon(icon_name, ACCENT))
                btn.setIconSize(btn.iconSize())
                btn.setStyleSheet(f"""
                    QPushButton {{
                        text-align: left;
                        padding: 10px 15px;
                        font-size: 14px;
                        font-weight: 500;
                        color: {ACCENT};
                        border: none;
                        border-radius: 8px;
                        background-color: {SURFACE_ELEVATED};
                    }}
                """)
                btn.clicked.connect(lambda checked=False, n=name: self.category_selected.emit(n))
            else:
                # Disabled / "Coming soon" item styling
                btn.setIcon(get_icon(icon_name, TEXT_SECONDARY))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        text-align: left;
                        padding: 10px 15px;
                        font-size: 14px;
                        font-weight: 400;
                        color: {TEXT_SECONDARY};
                        border: none;
                        background-color: transparent;
                        border-radius: 8px;
                    }}
                    QPushButton:disabled {{
                        color: {TEXT_SECONDARY};
                    }}
                """)
                btn.setDisabled(True)

            layout.addWidget(btn)
            self.buttons[name] = btn

        # Add vertical spacer at the bottom to push all buttons to the top
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)
