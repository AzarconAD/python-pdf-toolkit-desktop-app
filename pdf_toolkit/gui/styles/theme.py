# Color Palette (Dark Mode MVP)
BG_PAGE = "#121317"
SURFACE = "#1B1D22"
SURFACE_ELEVATED = "#24262C"
BORDER = "#33353C"
TEXT_PRIMARY = "#EAEAEC"
TEXT_SECONDARY = "#9497A0"
ACCENT = "#4C8DFF"
TEXT_ON_ACCENT = "#0A1830"
SUCCESS = "#34D399"
ERROR = "#F87171"
WARNING = "#FBBF24"

def get_stylesheet() -> str:
    return f"""
QMainWindow, QWidget {{
    background-color: {BG_PAGE};
    color: {TEXT_PRIMARY};
}}

QLabel {{
    color: {TEXT_PRIMARY};
}}

QPushButton {{
    background-color: {SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 12px;
}}

QPushButton:hover {{
    background-color: {SURFACE_ELEVATED};
}}

QPushButton:disabled {{
    background-color: {BG_PAGE};
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER};
}}

QScrollBar:vertical {{
    border: none;
    background-color: {BG_PAGE};
    width: 12px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background-color: {BORDER};
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {TEXT_SECONDARY};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
    background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    border: none;
    background-color: {BG_PAGE};
    height: 12px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background-color: {BORDER};
    min-width: 20px;
    border-radius: 6px;
    margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {TEXT_SECONDARY};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
    background: none;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}
"""
