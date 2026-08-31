from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsRectItem, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QColor, QFont

class ResizeHandle(QGraphicsRectItem):
    def __init__(self, parent=None):
        # Centered on the tip
        super().__init__(-5, -5, 10, 10, parent)
        self.setBrush(QColor("#4C8DFF")) # Theme accent
        self.setPen(QPen(Qt.GlobalColor.transparent))
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        # Accept the event so we get mouseMoveEvents
        pass
        
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        parent = self.parentItem()
        if parent:
            new_w = max(30, event.scenePos().x() - parent.scenePos().x())
            new_h = max(30, event.scenePos().y() - parent.scenePos().y())
            
            if hasattr(parent, "setTextWidth"):
                parent.setTextWidth(new_w)
                parent.update_handle_pos()
            elif hasattr(parent, "setShapeRect"):
                from PySide6.QtCore import QRectF
                parent.setShapeRect(QRectF(0, 0, new_w, new_h))
            elif hasattr(parent, "setImageRect"):
                from PySide6.QtCore import QRectF
                parent.setImageRect(QRectF(0, 0, new_w, new_h))

import math
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPixmap

class ImageElementItem(QGraphicsPixmapItem):
    def __init__(self, image_path: str, page_index: int = 0, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        import os
        self.image_path = os.path.abspath(image_path)
        
        self.original_pixmap = QPixmap(image_path)
        # Preserve aspect ratio on initial placement with a reasonable default width
        w = 150
        ratio = self.original_pixmap.height() / max(1.0, self.original_pixmap.width())
        h = int(w * ratio)
        self.target_rect = QRectF(0, 0, w, h)
        
        self.setPixmap(self.original_pixmap.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        
        self.handle = ResizeHandle(self)
        self.update_handle_pos()
        
    def update_handle_pos(self):
        r = self.boundingRect()
        self.handle.setPos(r.width(), r.height())
        
    def setImageRect(self, r: QRectF):
        self.target_rect = r
        w = max(10, int(r.width()))
        h = max(10, int(r.height()))
        self.setPixmap(self.original_pixmap.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.update_handle_pos()
        
    def paint(self, painter, option, widget=None):
        from PySide6.QtWidgets import QStyle
        is_selected = self.isSelected()
        option.state &= ~QStyle.StateFlag.State_Selected
        
        super().paint(painter, option, widget)
        
        if is_selected:
            sel_pen = QPen(QColor("#4C8DFF"), 1, Qt.PenStyle.DashLine)
            painter.setPen(sel_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())
            self.handle.show()
        else:
            self.handle.hide()

class ShapeElementItem(QGraphicsItem):
    def __init__(self, shape_type="rectangle", color: QColor = None, fill: QColor = None, page_index: int = 0, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        from PySide6.QtGui import QColor
        self.shape_type = shape_type
        self.color = color if color else QColor("#000000")
        self.fill = fill
        self.stroke_width = 5
        self._rect = QRectF(0, 0, 100, 100)
        
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        
        self.handle = ResizeHandle(self)
        self.update_handle_pos()
        
    def boundingRect(self):
        hw = self.stroke_width / 2.0
        return self._rect.adjusted(-hw, -hw, hw, hw)
        
    def update_handle_pos(self):
        self.handle.setPos(self._rect.width(), self._rect.height())

    def setShapeRect(self, r: QRectF):
        self.prepareGeometryChange()
        self._rect = r
        self.update_handle_pos()
        
    def paint(self, painter, option, widget=None):
        from PySide6.QtWidgets import QStyle
        from PySide6.QtGui import QPolygonF
        is_selected = self.isSelected()
        option.state &= ~QStyle.StateFlag.State_Selected
        
        pen = QPen(self.color, self.stroke_width)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        
        if self.fill:
            painter.setBrush(self.fill)
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
        r = self._rect
        
        if self.shape_type == "rectangle":
            painter.drawRect(r)
        elif self.shape_type == "circle":
            painter.drawEllipse(r)
        elif self.shape_type == "line":
            painter.drawLine(r.topLeft(), r.bottomRight())
        elif self.shape_type == "arrow":
            painter.drawLine(r.topLeft(), r.bottomRight())
            p1 = r.topLeft()
            p2 = r.bottomRight()
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            length = math.hypot(dx, dy)
            if length > 0:
                ux, uy = dx/length, dy/length
                head_l = max(10, self.stroke_width * 3)
                head_w = head_l / 2.0
                cx = p2.x() - head_l * ux
                cy = p2.y() - head_l * uy
                p3_x = cx - head_w * uy
                p3_y = cy + head_w * ux
                p4_x = cx + head_w * uy
                p4_y = cy - head_w * ux
                
                poly = QPolygonF([p2, QPointF(p3_x, p3_y), QPointF(p4_x, p4_y)])
                painter.setBrush(self.fill if self.fill else self.color)
                painter.drawPolygon(poly)
                
        if is_selected:
            sel_pen = QPen(QColor("#4C8DFF"), 1, Qt.PenStyle.DashLine)
            painter.setPen(sel_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())
            self.handle.show()
        else:
            self.handle.hide()

from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPainterPath

class DrawElementItem(QGraphicsPathItem):
    def __init__(self, color: QColor, stroke_width: float, page_index: int = 0, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self.points = []
        self.color = color
        self.stroke_width = stroke_width
        
        pen = QPen(self.color, self.stroke_width)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        
    def add_point(self, pt: QPointF):
        self.points.append(pt)
        self._update_path()
        
    def set_points(self, points: list[QPointF]):
        self.points = points
        self._update_path()
        
    def erase_radius(self, center: QPointF, radius: float):
        cx, cy = center.x(), center.y()
        r2 = radius * radius
        
        any_erased = False
        valid_mask = []
        for pt in self.points:
            dist2 = (pt.x() - cx)**2 + (pt.y() - cy)**2
            if dist2 <= r2:
                valid_mask.append(False)
                any_erased = True
            else:
                valid_mask.append(True)
                
        if not any_erased:
            return None
            
        runs = []
        current_run = []
        for valid, pt in zip(valid_mask, self.points):
            if valid:
                current_run.append(pt)
            else:
                if len(current_run) >= 2:
                    runs.append(current_run)
                current_run = []
                
        if len(current_run) >= 2:
            runs.append(current_run)
            
        return runs
        
    def _update_path(self):
        if not self.points:
            return
        path = QPainterPath(self.points[0])
        # Using straight lineTo segments for exact fidelity to cursor path
        for p in self.points[1:]:
            path.lineTo(p)
        self.setPath(path)
        
    def paint(self, painter, option, widget=None):
        from PySide6.QtWidgets import QStyle
        is_selected = self.isSelected()
        option.state &= ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)
        
        if is_selected:
            sel_pen = QPen(QColor("#4C8DFF"), 1, Qt.PenStyle.DashLine)
            painter.setPen(sel_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())

class TextElementItem(QGraphicsTextItem):
    def __init__(self, text="New Text", color: QColor = None, page_index: int = 0, 
                 font_size: int = 16, font_family: str = "helv", 
                 bold: bool = False, italic: bool = False, align: str = "left", parent=None):
        super().__init__(text, parent)
        self.page_index = page_index
        
        self.is_bold = bold
        self.is_italic = italic
        self.align = align
        self.font_family = font_family
        self.font_size = font_size
        
        self.setFlags(
            QGraphicsTextItem.GraphicsItemFlag.ItemIsMovable | 
            QGraphicsTextItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsTextItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        
        from PySide6.QtGui import QColor, QTextOption
        self.setDefaultTextColor(color if color else QColor("#000000"))
        self.setTextWidth(150)
        
        self.handle = ResizeHandle(self)
        self.update_handle_pos()
        
        # Re-position handle when text height changes (e.g. word wrap or newlines)
        self.document().contentsChanged.connect(self.update_handle_pos)
        self._apply_formatting()
        
    def _apply_formatting(self):
        from PySide6.QtGui import QFont, QTextOption
        
        # Map core schema names to approximate system fonts for UI display
        family_map = {
            "helv": "Arial",
            "times": "Times New Roman",
            "cour": "Courier New"
        }
        
        font = QFont(family_map.get(self.font_family, "Arial"))
        font.setPointSizeF(float(self.font_size))
        font.setBold(self.is_bold)
        font.setItalic(self.is_italic)
        self.setFont(font)
        
        align_map = {
            "left": Qt.AlignmentFlag.AlignLeft,
            "center": Qt.AlignmentFlag.AlignCenter,
            "right": Qt.AlignmentFlag.AlignRight,
            "justify": Qt.AlignmentFlag.AlignJustify
        }
        
        option = QTextOption()
        option.setAlignment(align_map.get(self.align, Qt.AlignmentFlag.AlignLeft))
        self.document().setDefaultTextOption(option)
        self.update_handle_pos()
        
    def set_formatting(self, **kwargs):
        if "bold" in kwargs: self.is_bold = kwargs["bold"]
        if "italic" in kwargs: self.is_italic = kwargs["italic"]
        if "align" in kwargs: self.align = kwargs["align"]
        if "font_family" in kwargs: self.font_family = kwargs["font_family"]
        if "font_size" in kwargs: self.font_size = kwargs["font_size"]
        if "color" in kwargs: self.setDefaultTextColor(kwargs["color"])
        self._apply_formatting()
        
    def mouseDoubleClickEvent(self, event):
        if self.textInteractionFlags() == Qt.TextInteractionFlag.NoTextInteraction:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        
        # We need to clear selection manually if we want it completely deselected, 
        # but standard behavior allows staying selected after editing.
        # Ensure we clear the text cursor so it doesn't look active.
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        
        super().focusOutEvent(event)
        
    def update_handle_pos(self):
        r = self.boundingRect()
        self.handle.setPos(r.width(), r.height())
        
    def paint(self, painter, option, widget=None):
        # Override paint to hide the default Qt dotted outline and draw our own
        # We need to clear the state's selection flag so the super call doesn't draw it
        from PySide6.QtWidgets import QStyle
        is_selected = self.isSelected()
        option.state &= ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)
        
        if is_selected:
            pen = QPen(QColor("#4C8DFF"), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())
            self.handle.show()
        else:
            self.handle.hide()
