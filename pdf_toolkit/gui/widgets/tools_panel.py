from PySide6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout,
                                QLabel, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from gui.styles.theme import (SURFACE, SURFACE_ELEVATED, BORDER,
                               TEXT_PRIMARY, TEXT_SECONDARY, BG_PAGE)
from gui.utils.icons import get_icon

# ─── Tool data ───────────────────────────────────────────────────────────────
# Each item: (icon_name, label, tool_id_or_None, is_divider)
# tool_id=None + is_divider=True → separator line
# tool_id=None + enabled_cat=False → disabled "coming soon" row
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
        "enabled": False,
        "items": [
            ("optimize",     "Compress PDF",   None,             False),
        ],
    },
    "Edit": {
        "enabled": False,
        "items": [
            ("edit",         "Coming soon",    None,             False),
        ],
    },
    "Security": {
        "enabled": False,
        "items": [
            ("security",     "Protect PDF",      None,           False),
            ("security",     "Unlock PDF",       None,           False),
            ("security",     "Watermark",        None,           False),
            ("security",     "Add Page Numbers", None,           False),
        ],
    },
}


# ─── PanelRow ─────────────────────────────────────────────────────────────────
class PanelRow(QFrame):
    def __init__(self, icon_name: str, text: str,
                 selected: bool = False,
                 clickable: bool = True,
                 dim: bool = False,       # dim=True → TEXT_SECONDARY text, no hover fill
                 on_click=None,
                 parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._clickable = clickable
        self._dim = dim
        self._on_click = on_click
        self._selected = selected
        self._hovering = False

        self.setFixedHeight(34)
        if clickable and not dim:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon(icon_name, TEXT_SECONDARY, 16).pixmap(16, 16))
        icon_lbl.setStyleSheet("border: none; background: transparent;")

        # dim overrides clickable for text colour
        text_color = TEXT_SECONDARY if (dim or not clickable) else TEXT_PRIMARY
        self._text_lbl = QLabel(text)
        self._text_lbl.setStyleSheet(
            f"color: {text_color}; font-size: 13px; border: none; background: transparent;"
        )

        layout.addWidget(icon_lbl)
        layout.addWidget(self._text_lbl)
        layout.addStretch()

        self._refresh_style()

    def _refresh_style(self):
        if self._selected:
            bg = SURFACE_ELEVATED
        elif self._hovering and self._clickable and not self._dim:
            bg = SURFACE_ELEVATED
        else:
            bg = "transparent"
        self.setStyleSheet(f"""
            PanelRow {{
                background-color: {bg};
                border-radius: 6px;
                border: none;
            }}
        """)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._refresh_style()

    def enterEvent(self, event):
        super().enterEvent(event)
        if self._clickable:
            self._hovering = True
            self._refresh_style()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hovering = False
        self._refresh_style()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self._clickable and self._on_click and event.button() == Qt.MouseButton.LeftButton:
            self._on_click()


# ─── ToolsPanel ───────────────────────────────────────────────────────────────
class ToolsPanel(QWidget):
    # Emitted with tool_id string when a tool row is clicked
    tool_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        # On Windows, Popup windows with transparent background show black gaps.
        # Use an opaque container frame as the visual shell instead.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"ToolsPanel {{ background-color: {BG_PAGE}; border: none; }}")

        self._active_cat = "Convert"
        self._cat_rows: dict = {}

        # Outer layout: 8px top gap (visual separation from button), 6px between cards
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 8, 6, 6)
        outer.setSpacing(6)

        # ── Left card ────────────────────────────────────────────────────────
        self._left_card = QFrame()
        self._left_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._left_card.setFixedWidth(180)
        self._left_card.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        # 5 rows × 34px + 4 gaps × 2px + 16px padding = 194px
        _CAT_ENABLED = {"Convert", "Organize"}

        left_layout = QVBoxLayout(self._left_card)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(2)

        for cat in ("Convert", "Organize", "Optimize", "Edit", "Security"):
            icon_name = cat.lower()
            is_sel = (cat == self._active_cat)
            is_dim = cat not in _CAT_ENABLED
            row = PanelRow(
                icon_name, cat,
                selected=is_sel,
                clickable=True,
                dim=is_dim,
                on_click=lambda c=cat: self._switch_category(c),
            )
            self._cat_rows[cat] = row
            left_layout.addWidget(row)

        # Fix height to content — no stretch, no vertical expansion
        self._left_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        outer.addWidget(self._left_card, 0, Qt.AlignmentFlag.AlignTop)

        # ── Right card ───────────────────────────────────────────────────────
        self._right_card = QFrame()
        self._right_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._right_card.setFixedWidth(200)
        self._right_card.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        self._right_layout = QVBoxLayout(self._right_card)
        self._right_layout.setContentsMargins(8, 8, 8, 8)
        self._right_layout.setSpacing(2)

        self._populate_right("Convert")
        outer.addWidget(self._right_card, 0, Qt.AlignmentFlag.AlignTop)

    # ── Category switching ────────────────────────────────────────────────────
    def _switch_category(self, cat: str):
        if cat == self._active_cat:
            return
        self._cat_rows[self._active_cat].set_selected(False)
        self._active_cat = cat
        self._cat_rows[cat].set_selected(True)
        self._clear_right()
        self._populate_right(cat)

    def _clear_right(self):
        while self._right_layout.count():
            item = self._right_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _populate_right(self, cat: str):
        data = _TOOLS[cat]
        enabled = data["enabled"]

        for icon_name, label, tool_id, is_divider in data["items"]:
            if is_divider:
                div = QFrame()
                div.setFixedHeight(1)
                div.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                div.setStyleSheet(f"background-color: {BORDER}; border: none;")
                self._right_layout.addWidget(div)
            else:
                # Build click callback only for enabled tools with a real tool_id
                callback = None
                if enabled and tool_id:
                    callback = lambda tid=tool_id: self._on_tool_click(tid)

                row = PanelRow(icon_name, label,
                               clickable=enabled,
                               on_click=callback)
                self._right_layout.addWidget(row)

        self._right_layout.addStretch()
        self._right_card.adjustSize()
        self.adjustSize()

    def _on_tool_click(self, tool_id: str):
        # Emit signal before closing so receiver can act on it
        self.tool_selected.emit(tool_id)
        self.close()
