import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFileDialog, QFrame, QScrollArea,
                               QComboBox, QRadioButton, QSpinBox, QStackedWidget, QSpacerItem, QSizePolicy, QLineEdit, QSlider)
from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt, Signal

from gui.widgets.drop_zone import DropZone
from gui.widgets.page_thumbnail_grid import PageThumbnailGrid
from gui.utils.thumbnails import get_page_count, render_page_thumbnail
from gui.styles.theme import TEXT_PRIMARY, TEXT_SECONDARY, SURFACE, BORDER, ACCENT, ERROR, SUCCESS, SURFACE_ELEVATED, BG_PAGE, TEXT_ON_ACCENT
from gui.utils.icons import get_icon
from gui.utils.error_messages import friendly_message

from core.convert_to import pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, pdf_to_images
from core.convert_from import docx_to_pdf, xlsx_to_pdf, pptx_to_pdf, images_to_pdf
from core.organize import merge_pdfs, split_pdf, extract_pages, delete_pages, reorder_pages, rotate_pages
from core.security import compress_pdf, protect_pdf, unlock_pdf, add_watermark, add_page_numbers
from core.utils import IncorrectPasswordError
from PySide6.QtWidgets import QProgressDialog, QMessageBox, QApplication

class FilePreviewWidget(QFrame):
    remove_requested = Signal(str)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_pdf = file_path.lower().endswith('.pdf')
        self.grid = None
        self.preview_expanded = False
        self.preview_mode = 'reader'
        
        self.setStyleSheet(f"""
            FilePreviewWidget {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header (Info row)
        header_layout = QHBoxLayout()
        
        # Thumbnail or Icon
        if self.is_pdf:
            try:
                pixmap = render_page_thumbnail(self.file_path, 1, max_size=50)
                icon_lbl = QLabel()
                icon_lbl.setPixmap(pixmap)
                header_layout.addWidget(icon_lbl)
            except Exception:
                icon_lbl = QLabel()
                icon_lbl.setPixmap(get_icon("pdf", TEXT_SECONDARY, 32).pixmap(32, 32))
                header_layout.addWidget(icon_lbl)
        else:
            icon_lbl = QLabel()
            ext = os.path.splitext(file_path)[1].lower()
            icon_name = "pdf" # fallback
            if ext in ['.doc', '.docx']: icon_name = "word"
            elif ext in ['.xls', '.xlsx']: icon_name = "excel"
            elif ext in ['.ppt', '.pptx']: icon_name = "ppt"
            elif ext in ['.png', '.jpg', '.jpeg']: icon_name = "image"
            
            icon_lbl.setPixmap(get_icon(icon_name, TEXT_SECONDARY, 32).pixmap(32, 32))
            header_layout.addWidget(icon_lbl)
            
        header_layout.addSpacing(10)
        
        # Text info
        text_layout = QVBoxLayout()
        filename_lbl = QLabel(os.path.basename(file_path))
        filename_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 14px; border: none;")
        text_layout.addWidget(filename_lbl)
        
        if self.is_pdf:
            try:
                pages = get_page_count(file_path)
                pages_lbl = QLabel(f"{pages} page{'s' if pages != 1 else ''}")
                pages_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; border: none;")
                text_layout.addWidget(pages_lbl)
            except Exception:
                pass
                
        header_layout.addLayout(text_layout)
        header_layout.addStretch()
        
        # Preview Toggle Button removed as per request
            
        self.remove_btn = QPushButton()
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        self.remove_btn.setStyleSheet("border: none; background: transparent;")
        self.remove_btn.setIcon(get_icon("trash", TEXT_SECONDARY, 17))
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.file_path))
        header_layout.addWidget(self.remove_btn)
            
        self.main_layout.addLayout(header_layout)
        
        # Expandable Grid Area (State 3 - Tool Selection)
        if self.is_pdf:
            self.grid_container = QWidget()
            self.grid_layout = QVBoxLayout(self.grid_container)
            self.grid_layout.setContentsMargins(0, 15, 0, 0)
            
            try:
                self.grid = PageThumbnailGrid(self.file_path)
                self.grid_layout.addWidget(self.grid)
            except Exception as e:
                err_lbl = QLabel(f"Failed to load preview: {e}")
                err_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
                self.grid_layout.addWidget(err_lbl)
                
            self.grid_container.setVisible(False)
            self.main_layout.addWidget(self.grid_container)
            
            # Expandable Reader Area (State 2 - View Mode)
            self.reader_container = QWidget()
            self.reader_layout = QVBoxLayout(self.reader_container)
            self.reader_layout.setContentsMargins(0, 15, 0, 0)
            self.reader = None # Lazy loaded
            
            self.reader_container.setVisible(False)
            self.main_layout.addWidget(self.reader_container)

    def _toggle_preview(self):
        if self.preview_mode == 'grid':
            self.set_grid_expanded(not self.preview_expanded)
        else:
            self.set_reader_expanded(not getattr(self, 'reader_expanded', False))
            
    def set_reader_expanded(self, expanded: bool):
        if not hasattr(self, 'reader_container'): return
        self.reader_expanded = expanded
        
        if expanded and self.reader is None:
            # Lazy load DocumentReader
            from gui.widgets.document_reader import DocumentReader
            try:
                self.reader = DocumentReader(self.file_path)
                self.reader_layout.addWidget(self.reader)
            except Exception as e:
                err_lbl = QLabel(f"Failed to load document reader: {e}")
                err_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
                self.reader_layout.addWidget(err_lbl)
                
        self.reader_container.setVisible(expanded)
        if expanded and self.preview_expanded:
            self.set_grid_expanded(False)
            


    def set_grid_expanded(self, expanded: bool):
        if not hasattr(self, 'grid_container'): return
        self.preview_expanded = expanded
        
        if expanded:
            self.preview_mode = 'grid'
            self.grid_container.setVisible(True)
            if getattr(self, 'reader_expanded', False):
                self.set_reader_expanded(False)
        else:
            self.preview_mode = 'reader'
            self.grid_container.setVisible(False)

class UnifiedWorkspacePage(QWidget):
    """
    Unified Workspace Page - Handles multiple states.
    State 1: Empty State (Centered DropZone).
    State 2: Compact DropZone + File Previews.
    """
    tool_selected = Signal(str)
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_files = []
        self.current_tool_id = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Persistent Header ---
        header_widget = QWidget()
        header_widget.setStyleSheet(f"border-bottom: 1px solid {BORDER}; background-color: {SURFACE};")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(0)

        # Back button
        self.back_btn = QPushButton(" Back")
        self.back_btn.setIcon(get_icon("arrow-left", TEXT_SECONDARY, 16))
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {TEXT_SECONDARY};
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                color: {TEXT_PRIMARY};
            }}
        """)
        self.back_btn.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(self.back_btn)
        header_layout.addSpacing(16)

        from PySide6.QtGui import QPixmap
        from pathlib import Path
        app_icon = QLabel()
        logo_path = str(Path(__file__).parent.parent.parent / "assets" / "app_icon.png")
        pixmap = QPixmap(logo_path).scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        app_icon.setPixmap(pixmap)
        app_icon.setFixedSize(22, 22)
        app_icon.setStyleSheet("border: none; background: transparent;")
        
        app_title = QLabel("PDF ToolBox")
        app_title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 500; border: none; background: transparent;")
        
        header_layout.addWidget(app_icon)
        header_layout.addSpacing(10)
        header_layout.addWidget(app_title)
        header_layout.addStretch()

        main_layout.addWidget(header_widget)
        

        # --- Stacked Content ---
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # --- State 1, 2, 3 View ---
        self.workspace_view = QWidget()
        self.layout = QVBoxLayout(self.workspace_view)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        self.stack.addWidget(self.workspace_view)
        
        self.top_stretch = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.bottom_stretch = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        
        self.layout.addItem(self.top_stretch)
        
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._on_files_added)
        self.drop_zone.browse_clicked.connect(self._on_browse)
        self.layout.addWidget(self.drop_zone, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        self.layout.addSpacing(10)
        self.layout.addItem(self.bottom_stretch)
        
        # Scroll area for previews
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        
        self.scroll_content = QWidget()
        self.previews_layout = QVBoxLayout(self.scroll_content)
        self.previews_layout.setAlignment(Qt.AlignTop)
        self.previews_layout.setContentsMargins(0, 0, 0, 0)
        self.previews_layout.setSpacing(15)
        
        self.scroll.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll)
        self.scroll.setVisible(False)
        
        # Tool-specific controls area (State 3)
        self.controls_container = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_container)
        self.controls_layout.setContentsMargins(0, 10, 0, 10)
        
        # Split controls
        self.split_controls = QWidget()
        sl = QHBoxLayout(self.split_controls)
        sl.setContentsMargins(0, 0, 0, 0)
        self.radio_every_n = QRadioButton("Split every N pages")
        self.radio_every_n.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.radio_every_n.setChecked(True)
        self.spin_n = QSpinBox()
        self.spin_n.setRange(1, 9999)
        self.spin_n.setStyleSheet(f"background-color: transparent; color: {TEXT_PRIMARY}; border: 1px solid {BORDER};")
        self.radio_custom = QRadioButton("Custom ranges")
        self.radio_custom.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.radio_custom.toggled.connect(lambda checked: self._expand_all_grids(checked) if self.controls_container.isVisible() else None)
        sl.addWidget(self.radio_every_n)
        sl.addWidget(self.spin_n)
        sl.addSpacing(20)
        sl.addWidget(self.radio_custom)
        sl.addStretch()
        self.controls_layout.addWidget(self.split_controls)
        self.split_controls.setVisible(False)
        
        # Rotate controls
        self.rotate_controls = QWidget()
        rl = QHBoxLayout(self.rotate_controls)
        rl.setContentsMargins(0, 0, 0, 0)
        lbl_angle = QLabel("Angle:")
        lbl_angle.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.angle_combo = QComboBox()
        self.angle_combo.addItems(["90", "180", "270", "-90"])
        self.angle_combo.setStyleSheet(f"background-color: transparent; color: {TEXT_PRIMARY}; border: 1px solid {BORDER};")
        rl.addWidget(lbl_angle)
        rl.addWidget(self.angle_combo)
        rl.addStretch()
        self.controls_layout.addWidget(self.rotate_controls)
        self.rotate_controls.setVisible(False)
        
        # Compress controls
        self.compress_controls = QWidget()
        cl = QHBoxLayout(self.compress_controls)
        cl.setContentsMargins(0, 0, 0, 0)
        lbl_quality = QLabel("Quality:")
        lbl_quality.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Low", "Medium", "High"])
        self.quality_combo.setCurrentText("Medium")
        self.quality_combo.setStyleSheet(f"background-color: transparent; color: {TEXT_PRIMARY}; border: 1px solid {BORDER};")
        cl.addWidget(lbl_quality)
        cl.addWidget(self.quality_combo)
        cl.addStretch()
        self.controls_layout.addWidget(self.compress_controls)
        self.compress_controls.setVisible(False)
        
        # Password controls (for protect and unlock)
        self.password_controls = QWidget()
        pl = QHBoxLayout(self.password_controls)
        pl.setContentsMargins(0, 0, 0, 0)
        lbl_password = QLabel("Password:")
        lbl_password.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(f"background-color: transparent; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; padding: 4px;")
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.textChanged.connect(self._validate_password)
        pl.addWidget(lbl_password)
        pl.addWidget(self.password_input)
        pl.addStretch()
        self.controls_layout.addWidget(self.password_controls)
        self.password_controls.setVisible(False)
        
                # Watermark controls (Parent container)
        self.watermark_controls = QWidget()
        wl_main = QHBoxLayout(self.watermark_controls)
        wl_main.setContentsMargins(0, 0, 0, 0)
        wl_main.setSpacing(16)
        
        # --- LEFT: Settings Card ---
        self.wm_settings_card = QWidget()
        self.wm_settings_card.setObjectName("WmSettingsCard")
        self.wm_settings_card.setFixedWidth(280)
        self.wm_settings_card.setStyleSheet(f"QWidget#WmSettingsCard {{ background-color: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        ws_layout = QVBoxLayout(self.wm_settings_card)
        ws_layout.setContentsMargins(16, 16, 16, 16)
        ws_layout.setSpacing(14)
        
        # Header
        lbl_ws_head = QLabel("Watermark settings")
        lbl_ws_head.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 500;")
        ws_layout.addWidget(lbl_ws_head)
        
        # Mode Toggle (Pill Segmented Control)
        self.wm_mode_container = QWidget()
        self.wm_mode_container.setStyleSheet(f"QWidget {{ background-color: {BG_PAGE}; border-radius: 6px; padding: 2px; }}")
        wmode_layout = QHBoxLayout(self.wm_mode_container)
        wmode_layout.setContentsMargins(2, 2, 2, 2)
        wmode_layout.setSpacing(0)
        
        from PySide6.QtWidgets import QButtonGroup
        self.wm_mode_grp = QButtonGroup(self)
        
        self.wm_mode_text = QPushButton("Text")
        self.wm_mode_text.setCheckable(True)
        self.wm_mode_text.setChecked(True)
        self.wm_mode_text.setCursor(Qt.PointingHandCursor)
        
        self.wm_mode_image = QPushButton("Image")
        self.wm_mode_image.setCheckable(True)
        self.wm_mode_image.setCursor(Qt.PointingHandCursor)
        
        self.wm_mode_grp.addButton(self.wm_mode_text)
        self.wm_mode_grp.addButton(self.wm_mode_image)
        
        import sys
        TEXT_ON_ACCENT_LOCAL = getattr(sys.modules.get('gui.styles.theme'), 'TEXT_ON_ACCENT', '#0A1830')
        toggle_qss = f"""
            QPushButton {{
                background-color: transparent; color: {TEXT_SECONDARY}; border: none; border-radius: 4px; padding: 6px 0px; font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: {ACCENT}; color: {TEXT_ON_ACCENT_LOCAL};
            }}
        """
        self.wm_mode_text.setStyleSheet(toggle_qss)
        self.wm_mode_image.setStyleSheet(toggle_qss)
        
        wmode_layout.addWidget(self.wm_mode_text)
        wmode_layout.addWidget(self.wm_mode_image)
        ws_layout.addWidget(self.wm_mode_container)
        
        self.wm_mode_text.toggled.connect(self._on_watermark_mode_changed)
        
        # TEXT SECTION
        self.wm_text_widget = QWidget()
        wt_layout = QVBoxLayout(self.wm_text_widget)
        wt_layout.setContentsMargins(0, 0, 0, 0)
        wt_layout.setSpacing(6)
        lbl_wt = QLabel("Text")
        lbl_wt.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self.watermark_input = QLineEdit()
        self.watermark_input.setStyleSheet(f"background-color: {BG_PAGE}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; padding: 6px; border-radius: 4px;")
        self.watermark_input.setPlaceholderText("Enter watermark text")
        self.watermark_input.textChanged.connect(self._on_wm_text_changed)
        wt_layout.addWidget(lbl_wt)
        wt_layout.addWidget(self.watermark_input)
        
        # IMAGE SECTION
        self.wm_image_widget = QWidget()
        wi_layout = QVBoxLayout(self.wm_image_widget)
        wi_layout.setContentsMargins(0, 0, 0, 0)
        wi_layout.setSpacing(6)
        
        lbl_wi = QLabel("Image")
        lbl_wi.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        
        img_pick_layout = QHBoxLayout()
        img_pick_layout.setContentsMargins(0, 0, 0, 0)
        self.wm_img_btn = QPushButton("Select Image")
        self.wm_img_btn.setCursor(Qt.PointingHandCursor)
        self.wm_img_btn.setStyleSheet(f"background-color: {BG_PAGE}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; padding: 4px 8px; border-radius: 4px;")
        self.wm_img_btn.clicked.connect(self._select_watermark_image)
        self.wm_img_path = ""
        self.wm_img_lbl = QLabel("No image selected")
        self.wm_img_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        img_pick_layout.addWidget(self.wm_img_btn)
        img_pick_layout.addWidget(self.wm_img_lbl)
        img_pick_layout.addStretch()
        
        self.wm_scale_header = QLabel("Scale: 0.30")
        self.wm_scale_header.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; margin-top: 8px;")
        self.wm_scale_slider = QSlider(Qt.Horizontal)
        self.wm_scale_slider.setRange(1, 100)
        self.wm_scale_slider.setValue(30)
        self.wm_scale_slider.valueChanged.connect(lambda v: self.wm_scale_header.setText(f"Scale: {v/100.0:.2f}"))
        self.wm_scale_slider.sliderReleased.connect(self._trigger_auto_preview)
        
        wi_layout.addWidget(lbl_wi)
        wi_layout.addLayout(img_pick_layout)
        wi_layout.addWidget(self.wm_scale_header)
        wi_layout.addWidget(self.wm_scale_slider)
        
        self.wm_image_widget.setVisible(False)
        
        # SHARED SETTINGS (Position, Opacity)
        self.wm_shared_widget = QWidget()
        wp_layout = QVBoxLayout(self.wm_shared_widget)
        wp_layout.setContentsMargins(0, 0, 0, 0)
        wp_layout.setSpacing(14)
        
        pos_layout = QVBoxLayout()
        pos_layout.setContentsMargins(0, 0, 0, 0)
        pos_layout.setSpacing(6)
        lbl_wp = QLabel("Position")
        lbl_wp.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self.watermark_pos_combo = QComboBox()
        self.watermark_pos_combo.addItems(["Center", "Diagonal", "Top", "Bottom"])
        self.watermark_pos_combo.setStyleSheet(f"background-color: {BG_PAGE}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; padding: 4px; border-radius: 4px;")
        self.watermark_pos_combo.currentIndexChanged.connect(lambda: self.wm_preview_timer.start())
        pos_layout.addWidget(lbl_wp)
        pos_layout.addWidget(self.watermark_pos_combo)
        
        op_layout = QVBoxLayout()
        op_layout.setContentsMargins(0, 0, 0, 0)
        op_layout.setSpacing(6)
        self.wm_op_header = QLabel("Opacity: 0.30")
        self.wm_op_header.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self.watermark_op_slider = QSlider(Qt.Horizontal)
        self.watermark_op_slider.setRange(10, 100)
        self.watermark_op_slider.setValue(30)
        self.watermark_op_slider.valueChanged.connect(lambda v: self.wm_op_header.setText(f"Opacity: {v/100.0:.2f}"))
        self.watermark_op_slider.sliderReleased.connect(self._trigger_auto_preview)
        op_layout.addWidget(self.wm_op_header)
        op_layout.addWidget(self.watermark_op_slider)
        
        wp_layout.addLayout(pos_layout)
        wp_layout.addLayout(op_layout)
        
        ws_layout.addWidget(self.wm_text_widget)
        ws_layout.addWidget(self.wm_image_widget)
        ws_layout.addWidget(self.wm_shared_widget)
        ws_layout.addStretch()
        
        # --- RIGHT: Preview Card ---
        self.wm_preview_card = QWidget()
        self.wm_preview_card.setObjectName("WmPreviewCard")
        self.wm_preview_card.setStyleSheet(f"QWidget#WmPreviewCard {{ background-color: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        wpc_layout = QVBoxLayout(self.wm_preview_card)
        wpc_layout.setContentsMargins(16, 16, 16, 16)
        wpc_layout.setSpacing(14)
        
        lbl_wpc_head = QLabel("Live preview")
        lbl_wpc_head.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 500;")
        wpc_layout.addWidget(lbl_wpc_head)
        
        self.wm_preview_scroll = QScrollArea()
        self.wm_preview_scroll.setWidgetResizable(True)
        self.wm_preview_scroll.setStyleSheet(f"QScrollArea {{ background-color: {BG_PAGE}; border-radius: 8px; border: none; }}")
        
        self.wm_preview_container = QWidget()
        self.wm_preview_container.setStyleSheet("background-color: transparent;")
        self.wm_preview_layout = QVBoxLayout(self.wm_preview_container)
        self.wm_preview_layout.setAlignment(Qt.AlignCenter)
        
        self._show_wm_placeholder()
        
        self.wm_preview_scroll.setWidget(self.wm_preview_container)
        wpc_layout.addWidget(self.wm_preview_scroll)
        
        # Add cards to main watermark layout
        wl_main.addWidget(self.wm_settings_card)
        wl_main.addWidget(self.wm_preview_card, 1) # stretch factor 1 so preview takes remaining space
        
        self.controls_layout.addWidget(self.watermark_controls)
        self.watermark_controls.setVisible(False)
        
        # Auto-preview debounce timer
        self.wm_preview_timer = QTimer(self)
        self.wm_preview_timer.setSingleShot(True)
        self.wm_preview_timer.setInterval(600)
        self.wm_preview_timer.timeout.connect(self._trigger_auto_preview)

        # Page numbers controls
        self.page_numbers_controls = QWidget()
        pnl = QHBoxLayout(self.page_numbers_controls)
        pnl.setContentsMargins(0, 0, 0, 0)
        
        lbl_pnp = QLabel("Position:")
        lbl_pnp.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.pn_pos_combo = QComboBox()
        self.pn_pos_combo.addItems(["Bottom-Center", "Bottom-Right", "Top-Center", "Top-Right"])
        self.pn_pos_combo.setStyleSheet(f"background-color: transparent; color: {TEXT_PRIMARY}; border: 1px solid {BORDER};")
        
        lbl_pns = QLabel("Start at:")
        lbl_pns.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.pn_start_spin = QSpinBox()
        self.pn_start_spin.setRange(-9999, 9999)
        self.pn_start_spin.setValue(1)
        self.pn_start_spin.setStyleSheet(f"background-color: transparent; color: {TEXT_PRIMARY}; border: 1px solid {BORDER};")
        
        pnl.addWidget(lbl_pnp)
        pnl.addWidget(self.pn_pos_combo)
        pnl.addSpacing(20)
        pnl.addWidget(lbl_pns)
        pnl.addWidget(self.pn_start_spin)
        pnl.addStretch()
        
        self.controls_layout.addWidget(self.page_numbers_controls)
        self.page_numbers_controls.setVisible(False)
        
        self.layout.addWidget(self.controls_container)
        self.controls_container.setVisible(False)
        
        # Bottom action button
        self.action_btn = QPushButton("Process")
        self.action_btn.setFixedSize(140, 40)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT}; color: #ffffff;
                font-size: 14px; font-weight: bold; border-radius: 6px; border: none;
            }}
        """)
        self.action_btn.clicked.connect(self._on_action)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.action_btn)
        self.layout.addLayout(btn_layout)
        self.action_btn.setVisible(False)
        
        self.scroll.setVisible(False)
        self.layout.setAlignment(self.drop_zone, Qt.AlignCenter)
        
        self.tool_selected.connect(self._on_tool_selected)
        
        # --- State 4 View (Results) ---
        self.result_view = QWidget()
        result_outer_layout = QVBoxLayout(self.result_view)
        result_outer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.result_card = QWidget()
        self.result_card.setFixedWidth(480)
        self.result_card.setObjectName("ResultCard")
        self.result_card.setStyleSheet(f"""
            #ResultCard {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        
        self.result_layout = QVBoxLayout(self.result_card)
        self.result_layout.setContentsMargins(28, 28, 28, 28)
        self.result_layout.setSpacing(20)
        
        self.result_header_layout = QHBoxLayout()
        self.result_header_layout.setSpacing(12)
        
        self.result_icon = QLabel()
        self.result_icon.setFixedSize(24, 24)
        self.result_icon.setStyleSheet("border: none; background: transparent;")
        
        self.result_title = QLabel("Processing complete")
        self.result_title.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none; background: transparent;")
        from PySide6.QtGui import QFont
        font = self.result_title.font()
        font.setPointSize(17)
        font.setWeight(QFont.Medium)
        self.result_title.setFont(font)
        
        self.result_header_layout.addWidget(self.result_icon)
        self.result_header_layout.addWidget(self.result_title)
        self.result_header_layout.addStretch()
        
        self.result_badges_layout = QHBoxLayout()
        self.result_badges_layout.setSpacing(8)
        self.result_badges_layout.setAlignment(Qt.AlignLeft)
        
        self.success_badge = QLabel()
        self.success_badge.setStyleSheet(f"""
            background-color: rgba(52, 211, 153, 0.12);
            color: {SUCCESS}; font-size: 12px; font-weight: 500;
            border-radius: 6px; padding: 4px 10px; border: none;
        """)
        
        self.error_badge = QLabel()
        self.error_badge.setStyleSheet(f"""
            background-color: rgba(248, 113, 113, 0.12);
            color: {ERROR}; font-size: 12px; font-weight: 500;
            border-radius: 6px; padding: 4px 10px; border: none;
        """)
        
        self.result_badges_layout.addWidget(self.success_badge)
        self.result_badges_layout.addWidget(self.error_badge)
        
        self.output_path_label = QLabel("Output folder")
        self.output_path_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; border: none; background: transparent;")
        
        self.output_path_chip = QWidget()
        self.output_path_chip.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_PAGE};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
        """)
        chip_layout = QHBoxLayout(self.output_path_chip)
        chip_layout.setContentsMargins(10, 8, 10, 8)
        chip_layout.setSpacing(10)
        
        self.output_path_text = QLabel()
        self.output_path_text.setStyleSheet(f"color: {TEXT_SECONDARY}; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; border: none; background: transparent;")
        
        self.output_path_copy_btn = QPushButton()
        self.output_path_copy_btn.setFixedSize(16, 16)
        self.output_path_copy_btn.setCursor(Qt.PointingHandCursor)
        self.output_path_copy_btn.setStyleSheet("border: none; background: transparent;")
        self.output_path_copy_btn.setIcon(get_icon("copy", TEXT_SECONDARY, 16))
        
        self.output_path_copy_btn.clicked.connect(self._copy_output_path)
        
        chip_layout.addWidget(self.output_path_text, 1)
        chip_layout.addWidget(self.output_path_copy_btn, 0)
        
        self.result_list_scroll = QScrollArea()
        self.result_list_scroll.setWidgetResizable(True)
        self.result_list_scroll.setFrameShape(QFrame.NoFrame)
        self.result_list_scroll.setStyleSheet("background: transparent; border: none;")
        self.result_list_scroll.setMaximumHeight(200)
        
        self.result_list_content = QWidget()
        self.result_list_content.setStyleSheet("background: transparent;")
        self.result_list_layout = QVBoxLayout(self.result_list_content)
        self.result_list_layout.setAlignment(Qt.AlignTop)
        self.result_list_layout.setContentsMargins(0, 0, 0, 0)
        self.result_list_scroll.setWidget(self.result_list_content)
        
        btn_layout_res = QHBoxLayout()
        btn_layout_res.setSpacing(10)
        
        self.start_over_btn = QPushButton("Start over")
        self.start_over_btn.setFixedHeight(40)
        self.start_over_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_over_btn.setObjectName("StartOverBtn")
        self.start_over_btn.setStyleSheet(f"""
            #StartOverBtn {{
                background-color: {ACCENT}; color: {TEXT_ON_ACCENT};
                font-size: 14px; font-weight: 500; border-radius: 6px; border: none; padding: 0 15px;
            }}
            #StartOverBtn:hover {{
                opacity: 0.9;
                background-color: #3A7CE0;
            }}
        """)
        self.start_over_btn.clicked.connect(self._on_start_over)
        
        btn_layout_res.addWidget(self.start_over_btn)
        
        self.result_layout.addLayout(self.result_header_layout)
        self.result_layout.addLayout(self.result_badges_layout)
        self.result_layout.addSpacing(10)
        self.result_layout.addWidget(self.output_path_label)
        self.result_layout.addWidget(self.output_path_chip)
        self.result_layout.addSpacing(10)
        self.result_layout.addWidget(self.result_list_scroll)
        self.result_layout.addSpacing(10)
        self.result_layout.addLayout(btn_layout_res)
        
        result_outer_layout.addStretch()
        result_outer_layout.addWidget(self.result_card, alignment=Qt.AlignHCenter)
        result_outer_layout.addStretch()
        
        self.stack.addWidget(self.result_view)

    def _on_browse(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "All Files (*)")
        if files:
            self._on_files_added(files)
            
    def _reset_to_state1(self):
        self.selected_files = []
        while self.previews_layout.count():
            item = self.previews_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        self.drop_zone.set_compact(False)
        self.scroll.setVisible(False)
        self.controls_container.setVisible(False)
        self.action_btn.setVisible(False)
        self.current_tool_id = None
        self.layout.setAlignment(self.drop_zone, Qt.AlignHCenter)
        self.top_stretch.changeSize(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.bottom_stretch.changeSize(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.invalidate()
        
        self.stack.setCurrentWidget(self.workspace_view)
        
    def _on_start_over(self):
        wrong_file_names = []
        if hasattr(self, 'last_results'):
            for fname, success, err_msg in self.last_results:
                if not success and ("tool needs a" in err_msg or "valid PDF" in err_msg or "Invalid input" in err_msg or "Invalid file extension" in err_msg):
                    wrong_file_names.append(fname)
                    
        if wrong_file_names:
            for fname in wrong_file_names:
                for fpath in list(self.selected_files):
                    import os
                    if os.path.basename(fpath) == fname:
                        self._remove_file(fpath)
            
            if self.selected_files:
                self.stack.setCurrentWidget(self.workspace_view)
                self.last_results = []
                return
                
        self.last_results = []
        self.back_requested.emit()

    def _on_files_added(self, files):
        self.selected_files.extend(files)
        
        # Transition to State 2
        self.top_stretch.changeSize(0, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.bottom_stretch.changeSize(0, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.layout.invalidate()
        
        self.layout.setAlignment(self.drop_zone, Qt.AlignTop)
        self.drop_zone.set_compact(True)
        self.scroll.setVisible(True)
        
        for f in files:
            preview = FilePreviewWidget(f)
            preview.remove_requested.connect(self._remove_file)
            self.previews_layout.addWidget(preview)
            
        if self.current_tool_id:
            self._on_tool_selected(self.current_tool_id)
            
    def _remove_file(self, file_path: str):
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
            
        for i in range(self.previews_layout.count()):
            item = self.previews_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), FilePreviewWidget):
                if item.widget().file_path == file_path:
                    item.widget().deleteLater()
                    
        if not self.selected_files:
            self._reset_to_state1()
            
    def _on_watermark_mode_changed(self):
        is_text = self.wm_mode_text.isChecked()
        self.wm_text_widget.setVisible(is_text)
        self.wm_image_widget.setVisible(not is_text)
        self._validate_watermark()
        self.wm_preview_timer.start()
        
    def _select_watermark_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Watermark Image", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.wm_img_path = file
            import os
            self.wm_img_lbl.setText(os.path.basename(file))
        self._validate_watermark()
        self.wm_preview_timer.start()

    def _validate_watermark(self):
        if self.current_tool_id == "watermark":
            self._on_tool_selected(self.current_tool_id)

    def _validate_password(self):
        if self.current_tool_id in ["protect", "unlock"]:
            self._on_tool_selected(self.current_tool_id)

    def _on_tool_selected(self, tool_id: str):
        self.current_tool_id = tool_id
        # Update action button text
        action_names = {
            "pdf_to_docx": "Convert to Word", "pdf_to_xlsx": "Convert to Excel",
            "pdf_to_pptx": "Convert to PPT", "pdf_to_images": "Convert to Images",
            "docx_to_pdf": "Convert to PDF", "xlsx_to_pdf": "Convert to PDF",
            "pptx_to_pdf": "Convert to PDF", "images_to_pdf": "Convert to PDF",
            "merge": "Merge PDFs", "split": "Split PDF", "extract": "Extract Pages",
            "delete": "Delete Pages", "reorder": "Reorder Pages", "rotate": "Rotate Pages",
            "compress": "Compress PDF", "edit_text": "Edit Text",
            "encrypt": "Encrypt PDF", "decrypt": "Decrypt PDF"
        }
        self.action_btn.setText(action_names.get(tool_id, "Process"))
        
        # Show/Hide specific controls
        self.split_controls.setVisible(tool_id == "split")
        self.rotate_controls.setVisible(tool_id == "rotate")
        self.compress_controls.setVisible(tool_id == "compress")
        self.password_controls.setVisible(tool_id in ["protect", "unlock"])
        self.watermark_controls.setVisible(tool_id == "watermark")
        if tool_id != "watermark":
            self._show_wm_placeholder()
        self.page_numbers_controls.setVisible(tool_id == "page_numbers")
        
        has_controls = tool_id in ["split", "rotate", "compress", "protect", "unlock", "watermark", "page_numbers"]
        self.controls_container.setVisible(has_controls)
        
        # Auto-expand grids for tools that need page-level selection
        needs_page_selection = tool_id in ["extract", "delete", "reorder", "rotate"]
        
        # If split is selected, expand only if custom is selected
        if tool_id == "split" and self.radio_custom.isChecked():
            needs_page_selection = True
            
        self._expand_all_grids(needs_page_selection)
        
        # Determine valid input for action button
        if len(self.selected_files) > 0:
            if tool_id == "merge" and len(self.selected_files) < 2:
                self.action_btn.setVisible(False)
            elif tool_id in ["compress", "protect", "unlock", "watermark", "page_numbers"] and len(self.selected_files) > 1:
                self.action_btn.setVisible(False)
            elif tool_id in ["protect", "unlock"] and not self.password_input.text():
                self.action_btn.setVisible(False)
            elif tool_id == "watermark":
                if self.wm_mode_text.isChecked() and not self.watermark_input.text():
                    self.action_btn.setVisible(False)
                elif not self.wm_mode_text.isChecked() and not getattr(self, "wm_img_path", ""):
                    self.action_btn.setVisible(False)
                else:
                    self.action_btn.setVisible(True)
            else:
                self.action_btn.setVisible(True)
        else:
            self.action_btn.setVisible(False)
            
    def _expand_all_grids(self, expanded: bool):
        for i in range(self.previews_layout.count()):
            widget = self.previews_layout.itemAt(i).widget()
            if isinstance(widget, FilePreviewWidget) and widget.is_pdf:
                widget.set_grid_expanded(expanded)

    def _copy_output_path(self):
        if hasattr(self, '_current_output_path'):
            QApplication.clipboard().setText(self._current_output_path)

    def _show_wm_placeholder(self):
        while self.wm_preview_layout.count():
            child = self.wm_preview_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.wm_preview_layout.setAlignment(Qt.AlignCenter)
        self.wm_preview_placeholder = QLabel("Rendered page will appear here")
        self.wm_preview_placeholder.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        self.wm_preview_placeholder.setAlignment(Qt.AlignCenter)
        self.wm_preview_layout.addWidget(self.wm_preview_placeholder)

    def _on_wm_text_changed(self):
        self._validate_watermark()
        self.wm_preview_timer.start()
        
    def _trigger_auto_preview(self):
        if self.current_tool_id != "watermark":
            return
        if self.wm_mode_text.isChecked() and not self.watermark_input.text():
            self._show_wm_placeholder()
            return
        elif not self.wm_mode_text.isChecked() and not getattr(self, "wm_img_path", ""):
            self._show_wm_placeholder()
            return
        if not self.selected_files:
            self._show_wm_placeholder()
            return
        self._on_preview_action()

    def _on_preview_action(self):
        fpaths = self.selected_files
        if not fpaths:
            return
        
        fpath = fpaths[0]
        
        import tempfile, os
        from gui.utils.error_messages import friendly_message
        
        fd, temp_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        os.remove(temp_path)
        
        # Show lightweight rendering indicator inline
        while self.wm_preview_layout.count():
            child = self.wm_preview_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.wm_preview_layout.setAlignment(Qt.AlignCenter)
        lbl_rendering = QLabel("Rendering...")
        from gui.styles.theme import TEXT_SECONDARY
        lbl_rendering.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; font-weight: bold;")
        lbl_rendering.setAlignment(Qt.AlignCenter)
        self.wm_preview_layout.addWidget(lbl_rendering)
        QApplication.processEvents()
        
        try:
            if self.wm_mode_text.isChecked():
                from core.security import add_watermark
                args = [self.watermark_input.text(), self.watermark_op_slider.value() / 100.0, self.watermark_pos_combo.currentText().lower()]
                temp_path = str(add_watermark(fpath, temp_path, *args))
            else:
                from core.security import add_image_watermark
                args = [self.wm_img_path, self.watermark_op_slider.value() / 100.0, self.watermark_pos_combo.currentText().lower(), self.wm_scale_slider.value() / 100.0]
                temp_path = str(add_image_watermark(fpath, temp_path, *args))
                
            from gui.utils.thumbnails import render_page_thumbnail
            
            # Clear previous preview pages
            while self.wm_preview_layout.count():
                child = self.wm_preview_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
            # Render only page 1 for preview
            pix = render_page_thumbnail(temp_path, 1, max_size=900)
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setPixmap(pix)
            self.wm_preview_layout.addWidget(lbl)
                

        except Exception as e:
            QMessageBox.warning(self, "Preview Error", friendly_message(e))
        finally:
            progress.close()
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _on_action(self):
        tid = self.current_tool_id
        if not tid or not self.selected_files: return
        
        tool_map = {
            "pdf_to_docx": (pdf_to_docx, "dir"), "pdf_to_xlsx": (pdf_to_xlsx, "dir"),
            "pdf_to_pptx": (pdf_to_pptx, "dir"), "pdf_to_images": (pdf_to_images, "dir"),
            "docx_to_pdf": (docx_to_pdf, "dir"), "xlsx_to_pdf": (xlsx_to_pdf, "dir"),
            "pptx_to_pdf": (pptx_to_pdf, "dir"), "split": (split_pdf, "dir"),
            "images_to_pdf": (images_to_pdf, "file"), "merge": (merge_pdfs, "file"),
            "extract": (extract_pages, "file_per_input"), "delete": (delete_pages, "file_per_input"),
            "reorder": (reorder_pages, "file_per_input"), "rotate": (rotate_pages, "file_per_input"), "compress": (compress_pdf, "file_per_input"), "protect": (protect_pdf, "file_per_input"), "unlock": (unlock_pdf, "file_per_input"), "watermark": (add_watermark, "file_per_input"), "page_numbers": (add_page_numbers, "file_per_input")
        }
        
        if tid not in tool_map:
            QMessageBox.information(self, "Coming Soon", f"Tool '{tid}' is not yet implemented.")
            return
            
        core_func, out_mode = tool_map[tid]
        
        if tid == "watermark" and not self.wm_mode_text.isChecked():
            from core.security import add_image_watermark
            core_func = add_image_watermark
        
        if out_mode == "dir":
            out_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
            if not out_path: return
        elif out_mode == "file":
            out_path, _ = QFileDialog.getSaveFileName(self, "Save Combined Result", "combined.pdf", "PDF Files (*.pdf)")
            if not out_path: return
        else: # file_per_input
            if len(self.selected_files) == 1:
                out_path, _ = QFileDialog.getSaveFileName(self, "Save Result", f"{tid}_result.pdf", "PDF Files (*.pdf)")
            else:
                out_path = QFileDialog.getExistingDirectory(self, "Select Output Directory for Results")
            if not out_path: return
            
        progress = QProgressDialog("Processing...", None, 0, 0, self)
        progress.setWindowTitle("Working")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        
        results = []
        
        if out_mode == "file":
            try:
                core_func(self.selected_files, out_path)
                results.append(("Combined File", True, ""))
            except Exception as e:
                results.append(("Combined File", False, friendly_message(e)))
        else:
            for i, fpath in enumerate(self.selected_files):
                fname = os.path.basename(fpath)
                try:
                    if out_mode == "file_per_input" and len(self.selected_files) > 1:
                        file_out_path = os.path.join(out_path, f"result_{fname}")
                    else:
                        file_out_path = out_path
                        
                    args = []
                    if tid == "split":
                        pages_per_file = 1
                        ranges = None
                        if self.radio_custom.isChecked():
                            widget = self.previews_layout.itemAt(i).widget()
                            if hasattr(widget, 'grid') and widget.grid:
                                selected = sorted(widget.grid.get_selected_pages())
                                if not selected: raise ValueError("No pages selected for custom split.")
                                ranges = []
                                start = end = selected[0]
                                for p in selected[1:]:
                                    if p == end + 1: end = p
                                    else:
                                        ranges.append([start, end])
                                        start = end = p
                                ranges.append([start, end])
                        else:
                            pages_per_file = self.spin_n.value()
                        args = [pages_per_file, ranges]
                        
                    elif tid in ["extract", "delete", "reorder", "rotate"]:
                        widget = self.previews_layout.itemAt(i).widget()
                        if not hasattr(widget, 'grid') or not widget.grid:
                            raise ValueError("Preview grid missing for page selection.")
                            
                        if tid in ["extract", "delete"]:
                            selected = widget.grid.get_selected_pages()
                            if not selected: raise ValueError("No pages selected.")
                            args = [selected]
                        elif tid == "reorder":
                            args = [widget.grid.get_page_order()]
                        elif tid == "rotate":
                            selected = widget.grid.get_selected_pages() or None
                            args = [int(self.angle_combo.currentText()), selected]
                            
                    elif tid == "compress":
                        args = [self.quality_combo.currentText().lower()]
                    elif tid in ["protect", "unlock"]:
                        args = [self.password_input.text()]
                    elif tid == "watermark":
                        if self.wm_mode_text.isChecked():
                            args = [self.watermark_input.text(), self.watermark_op_slider.value() / 100.0, self.watermark_pos_combo.currentText().lower()]
                        else:
                            args = [self.wm_img_path, self.watermark_op_slider.value() / 100.0, self.watermark_pos_combo.currentText().lower(), self.wm_scale_slider.value() / 100.0]
                    elif tid == "page_numbers":
                        args = [self.pn_pos_combo.currentText().lower(), self.pn_start_spin.value()]
                            
                    if args:
                        core_func(fpath, file_out_path, *args)
                    else:
                        core_func(fpath, file_out_path)
                        
                    results.append((fname, True, ""))
                except IncorrectPasswordError as e:
                    progress.close()
                    QMessageBox.warning(self, "Incorrect Password", friendly_message(e))
                    return
                except Exception as e:
                    results.append((fname, False, friendly_message(e)))
                    
        progress.close()
        
        self.last_results = results
        
        successes = sum(1 for r in results if r[1])
        failures = len(results) - successes
        
        # Update header icon
        if failures > 0:
            self.result_icon.setPixmap(get_icon("alert-circle", ERROR, 24).pixmap(24, 24))
        else:
            self.result_icon.setPixmap(get_icon("check-circle", SUCCESS, 24).pixmap(24, 24))
            
        # Update badges
        if successes > 0:
            self.success_badge.setText(f"{successes} succeeded")
            self.success_badge.setVisible(True)
        else:
            self.success_badge.setVisible(False)
            
        if failures > 0:
            self.error_badge.setText(f"{failures} failed")
            self.error_badge.setVisible(True)
        else:
            self.error_badge.setVisible(False)
        
        # Update output path
        self._current_output_path = os.path.normpath(out_path)
        
        # Truncate text logic (elide middle)
        from PySide6.QtGui import QFontMetrics
        metrics = QFontMetrics(self.output_path_text.font())
        elided_text = metrics.elidedText(self._current_output_path, Qt.ElideMiddle, 380) # ~480 card - padding
        self.output_path_text.setText(elided_text)
        
        while self.result_list_layout.count():
            item = self.result_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        for fname, success, err_msg in results:
            row = QWidget()
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(0, 5, 0, 5)
            row_l.setAlignment(Qt.AlignTop)
            
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(16, 16)
            icon_lbl.setStyleSheet("border: none; background: transparent;")
            
            text_layout = QVBoxLayout()
            text_layout.setSpacing(2)
            
            fname_lbl = QLabel(fname)
            fname_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 500; border: none; background: transparent;")
            text_layout.addWidget(fname_lbl)
            
            if success:
                icon_lbl.setPixmap(get_icon("check", SUCCESS, 16).pixmap(16, 16))
            else:
                icon_lbl.setPixmap(get_icon("x", ERROR, 16).pixmap(16, 16))
                err_lbl = QLabel(err_msg)
                err_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; border: none; background: transparent;")
                text_layout.addWidget(err_lbl)
                
            row_l.addWidget(icon_lbl, 0, Qt.AlignTop | Qt.AlignLeft)
            row_l.addLayout(text_layout, 1)
            self.result_list_layout.addWidget(row)
            
        self.stack.setCurrentWidget(self.result_view)
