import pymupdf
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QKeyEvent

from gui.utils.thumbnails import render_page_thumbnail, get_page_count

class EditCanvas(QGraphicsView):
    # Signals
    page_changed = Signal(int, int) # current_page, total_pages
    active_tool_changed = Signal(str)
    
    """
    Canvas for rendering and eventually editing PDF pages.
    Currently renders a static page background and supports Left/Right arrow navigation.
    
    Coordinate mapping contract:
    - PDF Point coordinates (72 dpi, top-left origin): The native coordinate space of the PDF page.
    - Scene Pixel coordinates (top-left origin): The pixel space of the scaled background pixmap.
    - To map from Scene to PDF: pdf_x = scene_x / self.scale_factor
    - To map from PDF to Scene: scene_x = pdf_x * self.scale_factor
    """
    def __init__(self, pdf_path: str, initial_page: int = 0, parent=None):
        super().__init__(parent)
        
        # Create a temporary working copy so destructive live-actions (highlight/redact)
        # don't permanently modify the user's original file before they explicitly "Save"
        import tempfile, shutil, os
        fd, self.working_pdf_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        shutil.copy2(pdf_path, self.working_pdf_path)
        
        self.original_pdf_path = pdf_path
        self.pdf_path = self.working_pdf_path
        
        self.page_count = get_page_count(self.pdf_path)
        self.current_page = max(0, min(initial_page, self.page_count - 1))
        
        self.scene_obj = QGraphicsScene(self)
        self.setScene(self.scene_obj)
        
        from gui.styles.theme import BG_PAGE
        from PySide6.QtGui import QColor, QBrush
        self.setBackgroundBrush(QBrush(QColor(BG_PAGE)))
        
        # Visual setup
        from PySide6.QtGui import QPainter
        self.setRenderHint(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        self.bg_item = QGraphicsPixmapItem()
        self.scene_obj.addItem(self.bg_item)
        
        # PDF to Scene mapping scale factor
        self.scale_factor = 1.0
        
        # Setup UI layout containers (handled by EditPage)
        from PySide6.QtWidgets import QPushButton, QComboBox, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel
        from gui.utils.icons import get_icon
        from gui.styles.theme import TEXT_SECONDARY, ACCENT
        from PySide6.QtGui import QColor
        
        self.left_rail = QWidget()
        self.left_rail.setFixedWidth(64)
        self.left_rail.setStyleSheet("""
            QWidget { background-color: #1B1D22; border-right: 1px solid #33353C; }
            QPushButton { background: transparent; border: none; padding: 12px; border-radius: 6px; outline: none; }
            QPushButton:focus { outline: none; }
            QPushButton:hover { background-color: #24262C; }
            QPushButton:checked { background-color: #24262C; }
        """)
        rail_layout = QVBoxLayout(self.left_rail)
        rail_layout.setContentsMargins(8, 16, 8, 16)
        rail_layout.setSpacing(12)
        rail_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        def make_divider():
            d = QFrame()
            d.setFrameShape(QFrame.Shape.HLine)
            d.setStyleSheet("background-color: #33353C; border: none; min-height: 1px; max-height: 1px;")
            return d
            
        self.active_color = QColor("#000000")
        
        self.active_color_btn = QPushButton()
        self.active_color_btn.setToolTip("Color")
        self._update_color_btn_style()
        self.active_color_btn.clicked.connect(self._pick_active_color)
        rail_layout.addWidget(self.active_color_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        rail_layout.addWidget(make_divider())
        
        self.add_text_btn = QPushButton()
        self.add_text_btn.setToolTip("Add text")
        self.add_text_btn.setIcon(get_icon("letter-case", TEXT_SECONDARY, 20))
        self.add_text_btn.clicked.connect(self._add_text_element)
        self.add_text_btn.clicked.connect(lambda: self._update_tool_icons(context="Text"))
        rail_layout.addWidget(self.add_text_btn)
        
        self.add_shape_btn = QPushButton()
        self.add_shape_btn.setToolTip("Add shape")
        self.add_shape_btn.setIcon(get_icon("square", TEXT_SECONDARY, 20))
        self.add_shape_btn.clicked.connect(self._add_shape_element)
        self.add_shape_btn.clicked.connect(lambda: self._update_tool_icons(context="Shape"))
        rail_layout.addWidget(self.add_shape_btn)
        
        self.add_image_btn = QPushButton()
        self.add_image_btn.setToolTip("Add image")
        self.add_image_btn.setIcon(get_icon("photo", TEXT_SECONDARY, 20))
        self.add_image_btn.clicked.connect(self._add_image_element)
        self.add_image_btn.clicked.connect(lambda: self._update_tool_icons(context="Image"))
        rail_layout.addWidget(self.add_image_btn)
        
        self.add_sig_btn = QPushButton()
        self.add_sig_btn.setToolTip("Add signature")
        self.add_sig_btn.setIcon(get_icon("signature", TEXT_SECONDARY, 20))
        self.add_sig_btn.clicked.connect(self._add_signature_element)
        self.add_sig_btn.clicked.connect(lambda: self._update_tool_icons(context="Signature"))
        rail_layout.addWidget(self.add_sig_btn)
        
        rail_layout.addWidget(make_divider())
        
        self.draw_mode_btn = QPushButton()
        self.draw_mode_btn.setToolTip("Draw")
        self.draw_mode_btn.setCheckable(True)
        self.draw_mode_btn.setIcon(get_icon("pencil", TEXT_SECONDARY, 20))
        self.draw_mode_btn.clicked.connect(self._toggle_draw_mode)
        rail_layout.addWidget(self.draw_mode_btn)
        
        self.eraser_mode_btn = QPushButton()
        self.eraser_mode_btn.setToolTip("Eraser")
        self.eraser_mode_btn.setCheckable(True)
        self.eraser_mode_btn.setIcon(get_icon("eraser", TEXT_SECONDARY, 20))
        self.eraser_mode_btn.clicked.connect(self._toggle_eraser_mode)
        rail_layout.addWidget(self.eraser_mode_btn)
        
        rail_layout.addWidget(make_divider())
        
        self.select_mode_btn = QPushButton()
        self.select_mode_btn.setToolTip("Select text")
        self.select_mode_btn.setCheckable(True)
        self.select_mode_btn.setIcon(get_icon("text-recognition", TEXT_SECONDARY, 20))
        self.select_mode_btn.clicked.connect(self._toggle_select_mode)
        rail_layout.addWidget(self.select_mode_btn)
        
        rail_layout.addWidget(make_divider())
        
        self.crop_mode_btn = QPushButton()
        self.crop_mode_btn.setToolTip("Crop page")
        self.crop_mode_btn.setCheckable(True)
        self.crop_mode_btn.setIcon(get_icon("crop", TEXT_SECONDARY, 20))
        self.crop_mode_btn.clicked.connect(self._toggle_crop_mode)
        rail_layout.addWidget(self.crop_mode_btn)
        
        rail_layout.addStretch()
        
        # Top Strip Contextual Bar
        self.top_strip = QWidget()
        self.top_strip.setObjectName("TopStrip")
        self.top_strip.setFixedHeight(60)
        self.top_strip.setStyleSheet("""
            QWidget#TopStrip { background-color: #1B1D22; border-bottom: 1px solid #33353C; }
        """)
        self.top_strip_layout = QHBoxLayout(self.top_strip)
        self.top_strip_layout.setContentsMargins(16, 8, 16, 8)
        self.top_strip_layout.setSpacing(16)
        
        # Helper to create setting pills
        from gui.styles.theme import CONTEXT_PILL_STYLE, TEXT_SECONDARY, ACCENT
        from PySide6.QtWidgets import QButtonGroup, QFrame, QSpinBox
        from PySide6.QtGui import QIcon
        
        def create_pill(title: str):
            pill = QWidget()
            pill.setObjectName("SettingsPill")
            pill.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            
            layout = QHBoxLayout(pill)
            layout.setContentsMargins(12, 6, 12, 6)
            layout.setSpacing(0)
            layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            
            lbl = QLabel(title)
            lbl.setObjectName("PillLabel")
            layout.addWidget(lbl)
            layout.addSpacing(8)
            
            return pill, layout
        
        from gui.utils.icons import get_icon
        
        # Text context
        self.text_format_widget, text_layout = create_pill("Text")
        
        # Font family dropdown
        self.text_font_family = QComboBox()
        self.text_font_family.setObjectName("SettingsControl")
        self.text_font_family.addItems(["Helvetica", "Times", "Courier"])
        self.text_font_family.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        text_layout.addWidget(self.text_font_family)
        text_layout.addSpacing(6)
        
        # Font size spinbox
        self.text_font_size = QSpinBox()
        self.text_font_size.setObjectName("SettingsControl")
        self.text_font_size.setRange(8, 144)
        self.text_font_size.setValue(16)
        self.text_font_size.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        text_layout.addWidget(self.text_font_size)
        text_layout.addSpacing(8)
        
        # Bold button
        self.text_bold_btn = QPushButton("B")
        self.text_bold_btn.setObjectName("SettingsToggle")
        self.text_bold_btn.setCheckable(True)
        self.text_bold_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        bold_font = self.text_bold_btn.font()
        bold_font.setBold(True)
        bold_font.setPointSize(13)
        self.text_bold_btn.setFont(bold_font)
        text_layout.addWidget(self.text_bold_btn)
        text_layout.addSpacing(2)
        
        # Italic button
        self.text_italic_btn = QPushButton("I")
        self.text_italic_btn.setObjectName("SettingsToggle")
        self.text_italic_btn.setCheckable(True)
        self.text_italic_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        italic_font = self.text_italic_btn.font()
        italic_font.setItalic(True)
        italic_font.setPointSize(13)
        self.text_italic_btn.setFont(italic_font)
        text_layout.addWidget(self.text_italic_btn)
        text_layout.addSpacing(10)
        
        # Alignment icon buttons
        self.align_group = QButtonGroup(self)
        self.align_group.setExclusive(True)
        self.align_btns = {}
        
        for align_val, icon_name in [("left", "align-left"), ("center", "align-center"),
                                     ("right", "align-right"), ("justify", "align-justify")]:
            btn = QPushButton()
            btn.setObjectName("IconButtonGroupBtn")
            btn.setCheckable(True)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setIconSize(__import__('PySide6.QtCore', fromlist=['QSize']).QSize(18, 18))
            
            icon = QIcon()
            icon.addPixmap(get_icon(icon_name, TEXT_SECONDARY, 18).pixmap(18, 18), QIcon.Mode.Normal, QIcon.State.Off)
            icon.addPixmap(get_icon(icon_name, ACCENT, 18).pixmap(18, 18), QIcon.Mode.Normal, QIcon.State.On)
            btn.setIcon(icon)
            
            self.align_group.addButton(btn)
            self.align_btns[align_val] = btn
            text_layout.addWidget(btn)
            
        self.align_btns["left"].setChecked(True)
        
        # Apply stylesheet after all children exist
        self.text_format_widget.setStyleSheet(CONTEXT_PILL_STYLE)
        
        self.top_strip_layout.addWidget(self.text_format_widget)
        self.top_strip_layout.addStretch()
        
        # Connect text formatting
        self.text_font_family.currentTextChanged.connect(self._on_text_format_changed)
        self.text_font_size.valueChanged.connect(self._on_text_format_changed)
        self.text_bold_btn.toggled.connect(self._on_text_format_changed)
        self.text_italic_btn.toggled.connect(self._on_text_format_changed)
        for btn in self.align_btns.values():
            btn.toggled.connect(self._on_text_format_changed)
        
        # State for default text formatting
        self.active_text_bold = False
        self.active_text_italic = False
        self.active_text_align = "left"
        self.active_text_font = "helv"
        self.active_text_size = 16
        
        # Shape context
        self.shape_format_widget, shape_layout = create_pill("Shape")
        self.shape_picker = QComboBox()
        self.shape_picker.setObjectName("SettingsControl")
        self.shape_picker.addItems(["rectangle", "circle", "line", "arrow"])
        self.shape_picker.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        shape_layout.addWidget(self.shape_picker)
        self.shape_format_widget.setStyleSheet(CONTEXT_PILL_STYLE)
        self.top_strip_layout.addWidget(self.shape_format_widget)
        
        # Draw context
        self.draw_format_widget, draw_layout = create_pill("Draw")
        self.draw_width_spin = QSpinBox()
        self.draw_width_spin.setObjectName("SettingsControl")
        self.draw_width_spin.setRange(1, 50)
        self.draw_width_spin.setValue(5)
        self.draw_width_spin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.draw_width_spin.setSuffix(" px")
        draw_layout.addWidget(self.draw_width_spin)
        self.draw_format_widget.setStyleSheet(CONTEXT_PILL_STYLE)
        self.top_strip_layout.addWidget(self.draw_format_widget)
        
        # Eraser context
        self.eraser_format_widget, eraser_layout = create_pill("Eraser")
        self.eraser_radius_spin = QSpinBox()
        self.eraser_radius_spin.setObjectName("SettingsControl")
        self.eraser_radius_spin.setRange(5, 100)
        self.eraser_radius_spin.setValue(15)
        self.eraser_radius_spin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.eraser_radius_spin.setSuffix(" px")
        eraser_layout.addWidget(self.eraser_radius_spin)
        self.eraser_format_widget.setStyleSheet(CONTEXT_PILL_STYLE)
        self.top_strip_layout.addWidget(self.eraser_format_widget)
        
        # Select context
        self.select_format_widget, select_layout = create_pill("Select")
        self.highlight_btn = QPushButton("Highlight")
        self.highlight_btn.setObjectName("SettingsActionBtn")
        self.highlight_btn.setEnabled(False)
        self.highlight_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.highlight_btn.clicked.connect(self._apply_highlight)
        select_layout.addWidget(self.highlight_btn)
        select_layout.addSpacing(6)
        
        self.redact_btn = QPushButton("Redact")
        self.redact_btn.setObjectName("SettingsActionBtn")
        self.redact_btn.setEnabled(False)
        self.redact_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.redact_btn.clicked.connect(self._apply_redact)
        select_layout.addWidget(self.redact_btn)
        self.select_format_widget.setStyleSheet(CONTEXT_PILL_STYLE)
        self.top_strip_layout.addWidget(self.select_format_widget)
        
        self.top_strip_layout.addStretch()
        self.top_strip.hide()
        
        # Prevent UI controls from stealing focus from the canvas
        for widget in [self.left_rail, self.top_strip]:
            for child in widget.findChildren(QWidget):
                child.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.draw_mode_active = False
        self.eraser_mode_active = False
        self.select_mode_active = False
        self.crop_mode_active = False
        self.active_draw_item = None
        self.drag_rect_item = None
        self.crop_drag_rect_item = None
        self.text_selection_overlays = []
        self.selected_text_rects_pdf = []
        self.page_words = []
        
        self.load_page(self.current_page)
        
    def _on_text_format_changed(self):
        font_map = {"Helvetica": "helv", "Times": "times", "Courier": "cour"}
        self.active_text_font = font_map.get(self.text_font_family.currentText(), "helv")
        self.active_text_size = self.text_font_size.value()
        self.active_text_bold = self.text_bold_btn.isChecked()
        self.active_text_italic = self.text_italic_btn.isChecked()
        
        for align_val, btn in self.align_btns.items():
            if btn.isChecked():
                self.active_text_align = align_val
                break
        
        # Apply to selected text item if any
        from .edit_elements import TextElementItem
        selected = self.scene_obj.selectedItems()
        for item in selected:
            if isinstance(item, TextElementItem):
                item.set_formatting(
                    font_family=self.active_text_font,
                    font_size=self.active_text_size * self.scale_factor,
                    bold=self.active_text_bold,
                    italic=self.active_text_italic,
                    align=self.active_text_align
                )
                
    def _update_color_btn_style(self):
        # Create a proper circular color swatch visually using CSS
        color_hex = self.active_color.name()
        self.active_color_btn.setFixedSize(28, 28)
        self.active_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                border: 2px solid #33353C;
                border-radius: 14px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                border: 2px solid #EAEAEC;
            }}
        """)
        
    def _pick_active_color(self):
        from PySide6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(self.active_color, self, "Pick Color")
        if color.isValid():
            self.active_color = color
            self._update_color_btn_style()
            
    def _update_tool_icons(self, context=None):
        from gui.utils.icons import get_icon
        from gui.styles.theme import TEXT_SECONDARY, ACCENT
        
        # Determine current context/mode
        has_context = False
        
        # Hide all context controls first
        self.shape_format_widget.setVisible(False)
        self.draw_format_widget.setVisible(False)
        self.eraser_format_widget.setVisible(False)
        self.select_format_widget.setVisible(False)
        self.text_format_widget.setVisible(False)
        
        if context == "Shape":
            self.shape_format_widget.setVisible(True)
            has_context = True
        elif context == "Text":
            self.text_format_widget.setVisible(True)
            has_context = True
            
        self.draw_mode_btn.setIcon(get_icon("pencil", ACCENT if self.draw_mode_active else TEXT_SECONDARY, 20))
        self.eraser_mode_btn.setIcon(get_icon("eraser", ACCENT if self.eraser_mode_active else TEXT_SECONDARY, 20))
        self.select_mode_btn.setIcon(get_icon("text-recognition", ACCENT if self.select_mode_active else TEXT_SECONDARY, 20))
        self.crop_mode_btn.setIcon(get_icon("crop", ACCENT if self.crop_mode_active else TEXT_SECONDARY, 20))
        
        active_tool_str = "None"
        if context:
            active_tool_str = context
            
        if self.draw_mode_active:
            has_context = True
            self.draw_format_widget.setVisible(True)
            active_tool_str = "Draw"
        elif self.eraser_mode_active:
            has_context = True
            self.eraser_format_widget.setVisible(True)
            active_tool_str = "Eraser"
        elif self.select_mode_active:
            has_context = True
            self.select_format_widget.setVisible(True)
            has_sel = len(self.selected_text_rects_pdf) > 0
            self.highlight_btn.setEnabled(has_sel)
            self.redact_btn.setEnabled(has_sel)
            active_tool_str = "Select Text"
        elif self.crop_mode_active:
            active_tool_str = "Crop"
            
        self.top_strip.setVisible(has_context)
        self.active_tool_changed.emit(active_tool_str)

    def _toggle_draw_mode(self, checked):
        if checked and self.eraser_mode_active:
            self.eraser_mode_btn.setChecked(False)
            self._toggle_eraser_mode(False)
        if checked and self.select_mode_active:
            self.select_mode_btn.setChecked(False)
            self._toggle_select_mode(False)
        if checked and self.crop_mode_active:
            self.crop_mode_btn.setChecked(False)
            self._toggle_crop_mode(False)
        self.draw_mode_active = checked
        if checked:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._update_tool_icons()
            
    def _toggle_eraser_mode(self, checked):
        if checked and self.draw_mode_active:
            self.draw_mode_btn.setChecked(False)
            self._toggle_draw_mode(False)
        if checked and self.select_mode_active:
            self.select_mode_btn.setChecked(False)
            self._toggle_select_mode(False)
        if checked and self.crop_mode_active:
            self.crop_mode_btn.setChecked(False)
            self._toggle_crop_mode(False)
        self.eraser_mode_active = checked
        if checked:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._update_tool_icons()
            
    def _toggle_select_mode(self, checked):
        if checked and self.draw_mode_active:
            self.draw_mode_btn.setChecked(False)
            self._toggle_draw_mode(False)
        if checked and self.eraser_mode_active:
            self.eraser_mode_btn.setChecked(False)
            self._toggle_eraser_mode(False)
        if checked and self.crop_mode_active:
            self.crop_mode_btn.setChecked(False)
            self._toggle_crop_mode(False)
        self.select_mode_active = checked
        if checked:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._update_tool_icons()
            
    def _toggle_crop_mode(self, checked):
        if checked and self.draw_mode_active:
            self.draw_mode_btn.setChecked(False)
            self._toggle_draw_mode(False)
        if checked and self.eraser_mode_active:
            self.eraser_mode_btn.setChecked(False)
            self._toggle_eraser_mode(False)
        if checked and self.select_mode_active:
            self.select_mode_btn.setChecked(False)
            self._toggle_select_mode(False)
        self.crop_mode_active = checked
        if checked:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._update_tool_icons()
            
    def mousePressEvent(self, event):
        if self.draw_mode_active and event.button() == Qt.MouseButton.LeftButton:
            from .edit_elements import DrawElementItem
            self.active_draw_item = DrawElementItem(self.active_color, self.draw_width_spin.value(), page_index=self.current_page)
            self.scene_obj.addItem(self.active_draw_item)
            self.active_draw_item.add_point(self.mapToScene(event.pos()))
        elif self.eraser_mode_active and event.button() == Qt.MouseButton.LeftButton:
            self._erase_at(event.pos())
        elif self.select_mode_active and event.button() == Qt.MouseButton.LeftButton:
            from PySide6.QtWidgets import QGraphicsRectItem
            from PySide6.QtCore import QRectF
            from PySide6.QtGui import QColor, QPen
            self._clear_text_selection()
            self.drag_start_pos = self.mapToScene(event.pos())
            self.drag_rect_item = QGraphicsRectItem(QRectF(self.drag_start_pos, self.drag_start_pos))
            self.drag_rect_item.setBrush(QColor(76, 141, 255, 64))
            self.drag_rect_item.setPen(QPen(QColor("#4C8DFF"), 1))
            self.scene_obj.addItem(self.drag_rect_item)
        elif self.crop_mode_active and event.button() == Qt.MouseButton.LeftButton:
            from PySide6.QtWidgets import QGraphicsRectItem
            from PySide6.QtCore import QRectF
            from PySide6.QtGui import QColor, QPen
            self.drag_start_pos = self.mapToScene(event.pos())
            self.crop_drag_rect_item = QGraphicsRectItem(QRectF(self.drag_start_pos, self.drag_start_pos))
            self.crop_drag_rect_item.setBrush(QColor(52, 211, 153, 64)) # Success green, dim
            self.crop_drag_rect_item.setPen(QPen(QColor("#34D399"), 2, Qt.PenStyle.DashLine))
            self.scene_obj.addItem(self.crop_drag_rect_item)
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        if self.draw_mode_active and self.active_draw_item:
            self.active_draw_item.add_point(self.mapToScene(event.pos()))
        elif self.eraser_mode_active and event.buttons() & Qt.MouseButton.LeftButton:
            self._erase_at(event.pos())
        elif self.select_mode_active and self.drag_rect_item:
            from PySide6.QtCore import QRectF
            current_pos = self.mapToScene(event.pos())
            self.drag_rect_item.setRect(QRectF(self.drag_start_pos, current_pos).normalized())
        elif self.crop_mode_active and self.crop_drag_rect_item:
            from PySide6.QtCore import QRectF
            current_pos = self.mapToScene(event.pos())
            self.crop_drag_rect_item.setRect(QRectF(self.drag_start_pos, current_pos).normalized())
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        if self.draw_mode_active and self.active_draw_item and event.button() == Qt.MouseButton.LeftButton:
            self.active_draw_item = None
        elif self.select_mode_active and self.drag_rect_item and event.button() == Qt.MouseButton.LeftButton:
            sel_rect = self.drag_rect_item.rect()
            self.scene_obj.removeItem(self.drag_rect_item)
            self.drag_rect_item = None
            self._finalize_text_selection(sel_rect)
        elif self.crop_mode_active and self.crop_drag_rect_item and event.button() == Qt.MouseButton.LeftButton:
            crop_rect = self.crop_drag_rect_item.rect()
            self.scene_obj.removeItem(self.crop_drag_rect_item)
            self.crop_drag_rect_item = None
            self._apply_crop(crop_rect)
        else:
            super().mouseReleaseEvent(event)
            
    def _finalize_text_selection(self, sel_rect):
        from PySide6.QtWidgets import QGraphicsRectItem
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QColor
        
        for item in self.text_selection_overlays:
            self.scene_obj.removeItem(item)
        self.text_selection_overlays.clear()
        self.selected_text_rects_pdf = []
        
        for word in self.page_words:
            pdf_r = QRectF(word[0], word[1], word[2] - word[0], word[3] - word[1])
            scene_r = QRectF(pdf_r.x() * self.scale_factor, pdf_r.y() * self.scale_factor, 
                             pdf_r.width() * self.scale_factor, pdf_r.height() * self.scale_factor)
                             
            if sel_rect.intersects(scene_r):
                self.selected_text_rects_pdf.append([word[0], word[1], word[2], word[3]])
                ov = QGraphicsRectItem(scene_r)
                ov.setBrush(QColor(76, 141, 255, 100))
                ov.setPen(Qt.PenStyle.NoPen)
                self.scene_obj.addItem(ov)
                self.text_selection_overlays.append(ov)
                
        has_sel = len(self.selected_text_rects_pdf) > 0
        self.highlight_btn.setEnabled(has_sel)
        self.redact_btn.setEnabled(has_sel)
        self.highlight_btn.setVisible(has_sel)
        self.redact_btn.setVisible(has_sel)
        
    def _apply_crop(self, crop_rect):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.warning(self, "Confirm Crop",
                                    "This will permanently crop the page dimensions. Continue?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            from core.edit import crop_page
            import tempfile, shutil, os
            
            # Map scene rect to PDF rect
            x0 = crop_rect.x() / self.scale_factor
            y0 = crop_rect.y() / self.scale_factor
            x1 = (crop_rect.x() + crop_rect.width()) / self.scale_factor
            y1 = (crop_rect.y() + crop_rect.height()) / self.scale_factor
            
            fd, temp_out = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            
            try:
                crop_page(self.pdf_path, temp_out, self.current_page, x0, y0, x1, y1)
                shutil.move(temp_out, self.pdf_path)
            except Exception as e:
                if os.path.exists(temp_out):
                    os.remove(temp_out)
                QMessageBox.critical(self, "Crop Error", f"Failed to crop page: {e}")
                return
                
            self.load_page(self.current_page)
            
    def cleanup(self):
        """Cleans up the temporary working copy. Should be called when abandoning the edit session."""
        import os
        if hasattr(self, 'working_pdf_path') and self.working_pdf_path:
            try:
                if os.path.exists(self.working_pdf_path):
                    os.remove(self.working_pdf_path)
            except OSError:
                pass
            self.working_pdf_path = None
            
    def _apply_highlight(self):
        rects = self.get_selected_text_rects()
        if not rects:
            return
        from core.edit import highlight_text
        import tempfile, shutil, os
        fd, temp_out = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        
        highlight_text(self.pdf_path, temp_out, self.current_page, rects)
        shutil.move(temp_out, self.pdf_path)
        
        self._clear_text_selection()
        self.load_page(self.current_page)
        
    def _apply_redact(self):
        rects = self.get_selected_text_rects()
        if not rects:
            return
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.warning(self, "Confirm Redaction",
                                    "This will permanently remove the selected content. Continue?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            from core.edit import redact_text
            import tempfile, shutil, os
            fd, temp_out = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            
            redact_text(self.pdf_path, temp_out, self.current_page, rects)
            shutil.move(temp_out, self.pdf_path)
            
            self._clear_text_selection()
            self.load_page(self.current_page)
            
    def _clear_text_selection(self):
        for item in self.text_selection_overlays:
            self.scene_obj.removeItem(item)
        self.text_selection_overlays.clear()
        self.selected_text_rects_pdf = []
        self.highlight_btn.setEnabled(False)
        self.redact_btn.setEnabled(False)
        
    def get_selected_text_rects(self) -> list[list[float]]:
        return self.selected_text_rects_pdf
            
    def _erase_at(self, view_pos):
        from .edit_elements import DrawElementItem
        from PySide6.QtCore import QRectF
        scene_pos = self.mapToScene(view_pos)
        r = self.eraser_radius_spin.value()
        
        # Fast bounding box check to only check intersecting items
        eraser_rect = QRectF(scene_pos.x() - r, scene_pos.y() - r, r * 2, r * 2)
        items = self.scene_obj.items(eraser_rect)
        
        for item in items:
            if isinstance(item, DrawElementItem):
                new_runs = item.erase_radius(scene_pos, r)
                if new_runs is not None:
                    # Stroke was modified (points erased)
                    self.scene_obj.removeItem(item)
                    for run_points in new_runs:
                        new_item = DrawElementItem(item.color, item.stroke_width, page_index=item.page_index)
                        new_item.set_points(run_points)
                        self.scene_obj.addItem(new_item)
        
    def _add_text_element(self):
        from .edit_elements import TextElementItem
        from PySide6.QtCore import QRectF
        view_center = self.viewport().rect().center()
        scene_pos = self.mapToScene(view_center)
        
        while True:
            overlap = False
            for existing_item in self.scene_obj.items(QRectF(scene_pos.x(), scene_pos.y(), 10, 10)):
                if isinstance(existing_item, TextElementItem):
                    if (abs(existing_item.scenePos().x() - scene_pos.x()) < 5 and 
                        abs(existing_item.scenePos().y() - scene_pos.y()) < 5):
                        overlap = True
                        break
            if overlap:
                scene_pos.setX(scene_pos.x() + 20)
                scene_pos.setY(scene_pos.y() + 20)
            else:
                break
        
        item = TextElementItem(
            "New Text", color=self.active_color, page_index=self.current_page,
            font_size=self.active_text_size * self.scale_factor,
            font_family=self.active_text_font,
            bold=self.active_text_bold,
            italic=self.active_text_italic,
            align=self.active_text_align
        )
        item.setPos(scene_pos)
        self.scene_obj.addItem(item)
        
    def _add_shape_element(self):
        from .edit_elements import ShapeElementItem
        view_center = self.viewport().rect().center()
        scene_pos = self.mapToScene(view_center)
        
        shape_type = self.shape_picker.currentText()
        item = ShapeElementItem(shape_type, color=self.active_color, page_index=self.current_page)
        item.setPos(scene_pos)
        self.scene_obj.addItem(item)
        
    def _add_image_element(self):
        from PySide6.QtWidgets import QFileDialog
        from .edit_elements import ImageElementItem
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_name:
            view_center = self.viewport().rect().center()
            scene_pos = self.mapToScene(view_center)
            
            item = ImageElementItem(file_name, page_index=self.current_page)
            item.setPos(scene_pos)
            self.scene_obj.addItem(item)
            
    def _add_signature_element(self):
        from .signature_dialog import SignatureDialog
        from .edit_elements import ImageElementItem
        dialog = SignatureDialog(self)
        if dialog.exec() == SignatureDialog.DialogCode.Accepted and dialog.selected_path:
            view_center = self.viewport().rect().center()
            scene_pos = self.mapToScene(view_center)
            
            item = ImageElementItem(dialog.selected_path, page_index=self.current_page)
            item.setPos(scene_pos)
            self.scene_obj.addItem(item)
        
    def get_elements(self) -> list[dict]:
        from .edit_elements import TextElementItem, ShapeElementItem, ImageElementItem, DrawElementItem
        elements = []
        for item in self.scene_obj.items():
            if isinstance(item, TextElementItem):
                r = item.boundingRect()
                pos = item.scenePos()
                
                pdf_x = pos.x() / self.scale_factor
                pdf_y = pos.y() / self.scale_factor
                pdf_w = r.width() / self.scale_factor
                pdf_h = r.height() / self.scale_factor
                
                font_size = round(item.font().pointSizeF() / self.scale_factor, 2)
                
                elements.append({
                    "type": "text",
                    "page": item.page_index,
                    "x": pdf_x,
                    "y": pdf_y,
                    "width": pdf_w,
                    "height": pdf_h,
                    "content": item.toPlainText(),
                    "font_size": font_size,
                    "color": item.defaultTextColor().name(),
                    "bold": item.is_bold,
                    "italic": item.is_italic,
                    "align": item.align,
                    "font_family": item.font_family
                })
            elif isinstance(item, ShapeElementItem):
                r = item._rect
                pos = item.scenePos()
                
                pdf_x1 = (pos.x() + r.left()) / self.scale_factor
                pdf_y1 = (pos.y() + r.top()) / self.scale_factor
                pdf_x2 = (pos.x() + r.right()) / self.scale_factor
                pdf_y2 = (pos.y() + r.bottom()) / self.scale_factor
                
                elements.append({
                    "type": "shape",
                    "page": item.page_index,
                    "shape": item.shape_type,
                    "x1": pdf_x1,
                    "y1": pdf_y1,
                    "x2": pdf_x2,
                    "y2": pdf_y2,
                    "color": item.color.name(),
                    "stroke_width": item.stroke_width / self.scale_factor,
                    "fill": item.fill.name() if item.fill else None
                })
            elif isinstance(item, ImageElementItem):
                r = item.boundingRect()
                pos = item.scenePos()
                
                pdf_x = pos.x() / self.scale_factor
                pdf_y = pos.y() / self.scale_factor
                pdf_w = r.width() / self.scale_factor
                pdf_h = r.height() / self.scale_factor
                
                elements.append({
                    "type": "image",
                    "page": item.page_index,
                    "x": pdf_x,
                    "y": pdf_y,
                    "width": pdf_w,
                    "height": pdf_h,
                    "image_path": item.image_path
                })
            elif isinstance(item, DrawElementItem):
                points = [[p.x() / self.scale_factor, p.y() / self.scale_factor] for p in item.points]
                elements.append({
                    "type": "draw",
                    "page": item.page_index,
                    "points": points,
                    "color": item.color.name(),
                    "stroke_width": item.stroke_width / self.scale_factor
                })
        return elements
        
    def load_page(self, page_index: int):
        """Loads a 0-indexed page into the background and updates coordinate mapping."""
        self.current_page = max(0, min(page_index, self.page_count - 1))
        
        # Clear existing text selection when changing pages
        if hasattr(self, "text_selection_overlays"):
            for item in self.text_selection_overlays:
                self.scene_obj.removeItem(item)
            self.text_selection_overlays.clear()
            self.selected_text_rects_pdf = []
            
        import pymupdf
        doc = pymupdf.open(self.pdf_path)
        self.page_words = doc[self.current_page].get_text("words")
        doc.close()
        
        from ..utils.thumbnails import render_page_thumbnail
        pixmap = render_page_thumbnail(self.pdf_path, self.current_page + 1, max_size=900)
        self.bg_item.setPixmap(pixmap)
        
        # Calculate scale factor
        # Open quickly to read native page rect dimensions
        with pymupdf.open(self.pdf_path) as doc:
            page = doc.load_page(self.current_page)
            pdf_rect = page.rect
            longest_side = max(pdf_rect.width, pdf_rect.height)
            if longest_side > 0:
                actual_longest = max(pixmap.width(), pixmap.height())
                self.scale_factor = actual_longest / longest_side
            else:
                self.scale_factor = 1.0
                
        # Update scene rect to match exactly the pixmap size
        from PySide6.QtCore import QRectF
        rect = QRectF(pixmap.rect())
        self.scene_obj.setSceneRect(rect)
        self.bg_item.setPos(0, 0)
        
        # Toggle element visibility
        from .edit_elements import TextElementItem, ShapeElementItem, ImageElementItem, DrawElementItem
        for item in self.scene_obj.items():
            if isinstance(item, (TextElementItem, ShapeElementItem, ImageElementItem, DrawElementItem)):
                item.setVisible(item.page_index == self.current_page)
                
        self.page_changed.emit(self.current_page, self.page_count)
    def keyPressEvent(self, event: QKeyEvent):
        """Arrow keys navigate pages. Delete removes selected items. Other keys passed to super()."""
        from .edit_elements import TextElementItem
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            actively_editing = any(isinstance(i, TextElementItem) and i.hasFocus() for i in self.scene_obj.selectedItems())
            if actively_editing:
                super().keyPressEvent(event)
            else:
                for item in self.scene_obj.selectedItems():
                    self.scene_obj.removeItem(item)
        elif event.key() == Qt.Key.Key_Left:
            if self.current_page > 0:
                self.load_page(self.current_page - 1)
        elif event.key() == Qt.Key.Key_Right:
            if self.current_page < self.page_count - 1:
                self.load_page(self.current_page + 1)
        else:
            super().keyPressEvent(event)

