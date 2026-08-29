from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy

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

        # Define categories: (Name, is_enabled, tooltip)
        categories = [
            ("Convert", True, "Convert between PDF and other formats"),
            ("Organize", False, "Coming soon"),
            ("Optimize", False, "Coming soon"),
            ("Edit", False, "Coming soon"),
            ("Security", False, "Coming soon"),
        ]

        self.buttons = {}

        for name, is_enabled, tooltip in categories:
            btn = QPushButton(name)
            btn.setToolTip(tooltip)
            
            # Basic styling to make it look like a sidebar menu item
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 10px 15px;
                    font-size: 14px;
                    border: none;
                    border-radius: 5px;
                    background-color: transparent;
                }
                QPushButton:enabled:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:enabled:pressed {
                    background-color: #d0d0d0;
                }
                QPushButton:disabled {
                    color: #a0a0a0;
                }
            """)
            
            if not is_enabled:
                btn.setDisabled(True)
            else:
                # Capture the current name in the lambda to avoid late-binding issues
                btn.clicked.connect(lambda checked=False, n=name: self.category_selected.emit(n))

            layout.addWidget(btn)
            self.buttons[name] = btn

        # Add vertical spacer at the bottom to push all buttons to the top
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)
