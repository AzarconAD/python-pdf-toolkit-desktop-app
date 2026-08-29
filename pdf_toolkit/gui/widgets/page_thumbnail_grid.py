from PySide6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QLabel, QFrame, QApplication
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QMouseEvent, QDrag

from gui.utils.thumbnails import render_page_thumbnail, get_page_count
from gui.styles import theme


class ThumbnailTile(QFrame):
    clicked = Signal(int, QMouseEvent)

    def __init__(self, page_num: int, pixmap, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.is_selected = False
        self._drag_start_pos = None
        
        self.setFixedSize(120, 160)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        img_label = QLabel()
        img_label.setPixmap(pixmap)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setStyleSheet("border: none; background: transparent;")
        
        text_label = QLabel(f"Page {page_num}")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; border: none; background: transparent; font-size: 11px;")
        
        layout.addWidget(img_label)
        layout.addWidget(text_label)
        
        self._update_style()
        
    def set_selected(self, selected: bool):
        if self.is_selected != selected:
            self.is_selected = selected
            self._update_style()
            
    def _update_style(self):
        if self.is_selected:
            self.setStyleSheet(f"""
                ThumbnailTile {{
                    background-color: {theme.SURFACE_ELEVATED};
                    border: 2px solid {theme.ACCENT};
                    border-radius: 4px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                ThumbnailTile {{
                    background-color: {theme.SURFACE};
                    border: 1px solid {theme.BORDER};
                    border-radius: 4px;
                }}
            """)

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self.clicked.emit(self.page_num, event)

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not self._drag_start_pos:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.page_num))
        drag.setMimeData(mime_data)
        
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        drag.exec(Qt.DropAction.MoveAction)


class GridContainer(QWidget):
    dropped = Signal(int, int) # source_page_num, target_index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            source_page_num = int(event.mimeData().text())
            pos = event.position().toPoint()
            
            target_index = -1
            layout = self.layout()
            min_dist = float('inf')
            
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    w = item.widget()
                    center = w.geometry().center()
                    dist = (center.x() - pos.x())**2 + (center.y() - pos.y())**2
                    if dist < min_dist:
                        min_dist = dist
                        target_index = i
                        
            if target_index != -1:
                self.dropped.emit(source_page_num, target_index)
                event.acceptProposedAction()


class PageThumbnailGrid(QWidget):
    selectionChanged = Signal()

    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self._tiles = []
        self._current_cols = -1
        self._selected_pages = []  # Maintain selection order
        self._last_clicked_page = -1
        self._setup_ui()
        self._load_thumbnails()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.grid_container = GridContainer()
        self.grid_container.setStyleSheet(f"background-color: transparent;")
        self.grid_container.dropped.connect(self._on_tile_dropped)
        
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(16, 16, 16, 16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        main_layout.addWidget(self.grid_container)
        
    def _load_thumbnails(self):
        try:
            total_pages = get_page_count(self.pdf_path)
        except Exception:
            return
            
        for i in range(total_pages):
            page_num = i + 1
            pixmap = render_page_thumbnail(self.pdf_path, page_num, max_size=100)
            
            tile = ThumbnailTile(page_num, pixmap)
            tile.clicked.connect(self._on_tile_clicked)
            self._tiles.append(tile)
            
        self._reflow(force=True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow()
        
    def _reflow(self, force=False):
        if not self._tiles:
            return
            
        available_width = self.width() - 32
        tile_width = 120 + 16
        columns = max(1, available_width // tile_width)
        
        if columns == self._current_cols and not force:
            return
            
        self._current_cols = columns
        
        for tile in self._tiles:
            self.grid_layout.removeWidget(tile)
            
        for i, tile in enumerate(self._tiles):
            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(tile, row, col)

    def _on_tile_dropped(self, source_page_num: int, target_index: int):
        source_tile = next((t for t in self._tiles if t.page_num == source_page_num), None)
        if not source_tile:
            return
            
        current_index = self._tiles.index(source_tile)
        if current_index == target_index:
            return
            
        # Reorder
        self._tiles.pop(current_index)
        self._tiles.insert(target_index, source_tile)
        
        self._reflow(force=True)

    def _on_tile_clicked(self, page_num: int, event: QMouseEvent):
        modifiers = event.modifiers()
        is_ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        
        if is_shift and self._last_clicked_page != -1:
            last_idx = next((i for i, t in enumerate(self._tiles) if t.page_num == self._last_clicked_page), -1)
            curr_idx = next((i for i, t in enumerate(self._tiles) if t.page_num == page_num), -1)
            
            if last_idx != -1 and curr_idx != -1:
                start_idx = min(last_idx, curr_idx)
                end_idx = max(last_idx, curr_idx)
                
                if not is_ctrl:
                    self._selected_pages.clear()
                    
                for i in range(start_idx, end_idx + 1):
                    p = self._tiles[i].page_num
                    if p not in self._selected_pages:
                        self._selected_pages.append(p)
        else:
            if is_ctrl:
                if page_num in self._selected_pages:
                    self._selected_pages.remove(page_num)
                else:
                    self._selected_pages.append(page_num)
            else:
                self._selected_pages = [page_num]
                
            self._last_clicked_page = page_num
            
        self._update_all_tiles()
        self.selectionChanged.emit()
        
    def _update_all_tiles(self):
        for tile in self._tiles:
            tile.set_selected(tile.page_num in self._selected_pages)

    def get_selected_pages(self) -> list[int]:
        """Returns 1-indexed original page numbers in the order they were selected."""
        return list(self._selected_pages)

    def get_page_order(self) -> list[int]:
        """Returns the current visual order as 1-indexed original page numbers."""
        return [t.page_num for t in self._tiles]
