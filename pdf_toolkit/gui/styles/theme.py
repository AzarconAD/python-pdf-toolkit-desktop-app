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
    
CONTEXT_PILL_STYLE = f"""
QWidget#SettingsPill {{ 
    background-color: {SURFACE_ELEVATED}; 
    border: 1px solid {BORDER}; 
    border-radius: 8px; 
}}
QLabel#PillLabel {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
    font-weight: normal;
    background: transparent;
    border: none;
    padding: 0px 4px;
}}
QComboBox#SettingsControl {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    color: {TEXT_PRIMARY}; 
    padding: 0px 6px;
    border-radius: 6px;
    min-height: 28px;
    max-height: 28px;
    min-width: 90px;
    font-size: 13px;
    selection-background-color: {ACCENT};
}}
QComboBox#SettingsControl:hover {{
    border: 1px solid {TEXT_SECONDARY};
}}
QComboBox#SettingsControl QAbstractItemView {{
    background-color: {SURFACE_ELEVATED};
    border: 1px solid {BORDER};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT};
    selection-color: {TEXT_ON_ACCENT};
    padding: 4px;
}}
QSpinBox#SettingsControl {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    color: {TEXT_PRIMARY};
    padding: 0px 4px;
    border-radius: 6px;
    min-height: 28px;
    max-height: 28px;
    min-width: 70px;
    max-width: 80px;
    font-size: 13px;
}}
QSpinBox#SettingsControl:hover {{
    border: 1px solid {TEXT_SECONDARY};
}}
QPushButton#SettingsToggle {{
    background-color: transparent;
    border: none;
    color: {TEXT_PRIMARY};
    border-radius: 6px;
    min-width: 30px;
    max-width: 30px;
    min-height: 30px;
    max-height: 30px;
    font-size: 14px;
    padding: 0px;
}}
QPushButton#SettingsToggle:hover {{ 
    background: {BORDER};
}}
QPushButton#SettingsToggle:checked {{ 
    background: {ACCENT}; 
    color: {TEXT_ON_ACCENT}; 
}}
QPushButton#IconButtonGroupBtn {{
    background: transparent;
    border: none;
    border-radius: 4px;
    min-width: 30px;
    max-width: 30px;
    min-height: 30px;
    max-height: 30px;
    padding: 0px;
}}
QPushButton#IconButtonGroupBtn:hover {{
    background: {BORDER};
}}
QPushButton#SettingsActionBtn {{
    background-color: {ACCENT};
    color: {TEXT_ON_ACCENT};
    border: none;
    border-radius: 6px;
    padding: 0px 12px;
    min-height: 28px;
    max-height: 28px;
    font-weight: bold;
    font-size: 13px;
}}
QPushButton#SettingsActionBtn:hover {{
    background-color: #609AFF;
}}
QPushButton#SettingsActionBtn:disabled {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER};
}}
"""
