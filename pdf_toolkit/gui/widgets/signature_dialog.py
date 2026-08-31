from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, QInputDialog, QFileDialog, QWidget, QLabel
from PySide6.QtGui import QPainter, QPen, QPixmap, QIcon, QPainterPath
from PySide6.QtCore import Qt, QSize
from core.signature_storage import list_signatures, save_signature, delete_signature

class DrawPad(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 200)
        self.path = QPainterPath()
        self.setStyleSheet("background-color: white; border: 1px solid gray;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.path.moveTo(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.path.lineTo(event.pos())
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.white)
        pen = QPen(Qt.GlobalColor.black, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(self.path)

    def get_pixmap(self) -> QPixmap:
        # Render onto a transparent background so signature blends into PDF
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        pen = QPen(Qt.GlobalColor.black, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(self.path)
        painter.end()
        return pixmap

class SignatureDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Signatures")
        self.selected_path = None
        
        layout = QHBoxLayout(self)
        
        # Left side: list of saved signatures
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Saved Signatures:"))
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(100, 50))
        self.refresh_list()
        left_layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        self.use_btn = QPushButton("Use Selected")
        self.use_btn.clicked.connect(self.use_selected)
        self.del_btn = QPushButton("Delete")
        self.del_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(self.use_btn)
        btn_layout.addWidget(self.del_btn)
        left_layout.addLayout(btn_layout)
        layout.addLayout(left_layout)
        
        # Right side: Draw or Upload
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Draw New Signature:"))
        self.pad = DrawPad()
        right_layout.addWidget(self.pad)
        
        save_draw_btn = QPushButton("Save Drawn Signature")
        save_draw_btn.clicked.connect(self.save_drawn)
        right_layout.addWidget(save_draw_btn)
        
        right_layout.addSpacing(20)
        right_layout.addWidget(QLabel("Or Upload Signature Image:"))
        upload_btn = QPushButton("Upload Image")
        upload_btn.clicked.connect(self.upload_image)
        right_layout.addWidget(upload_btn)
        
        layout.addLayout(right_layout)

    def refresh_list(self):
        self.list_widget.clear()
        sigs = list_signatures()
        for sig in sigs:
            item = QListWidgetItem(sig["name"])
            item.setIcon(QIcon(sig["path"]))
            item.setData(Qt.ItemDataRole.UserRole, sig["path"])
            self.list_widget.addItem(item)
            
    def use_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self.selected_path = item.data(Qt.ItemDataRole.UserRole)
            self.accept()
            
    def delete_selected(self):
        item = self.list_widget.currentItem()
        if item:
            delete_signature(item.text())
            self.refresh_list()
            
    def save_drawn(self):
        if self.pad.path.isEmpty():
            return
        name, ok = QInputDialog.getText(self, "Signature Name", "Enter name:")
        if ok and name:
            save_signature(self.pad.get_pixmap(), name)
            self.refresh_list()
            self.pad.path = QPainterPath() # clear pad
            self.pad.update()
            
    def upload_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Upload Signature", "", "Images (*.png *.jpg *.jpeg)")
        if file_name:
            name, ok = QInputDialog.getText(self, "Signature Name", "Enter name:")
            if ok and name:
                save_signature(file_name, name)
                self.refresh_list()
