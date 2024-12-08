from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor

class LoadingIndicator(QWidget):
    def __init__(self, text="Loading...", parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        
        layout = QVBoxLayout(self)
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.setFixedSize(200, 100)
        self.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            border: 1px solid #ccc;
        """)
    
    def setText(self, text: str):
        """Update the loading indicator text."""
        self.label.setText(text)
    
    def start(self):
        self.timer.start(50)  # Update every 50ms
        self.show()
    
    def stop(self):
        self.timer.stop()
        self.hide()
    
    def rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw spinning circle
        center = self.rect().center()
        painter.translate(center)
        painter.rotate(self.angle)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#0084ff"))
        
        for i in range(8):
            painter.rotate(45)
            opacity = 0.3 + (i / 8) * 0.7
            painter.setOpacity(opacity)
            painter.drawEllipse(-5, -20, 10, 10) 