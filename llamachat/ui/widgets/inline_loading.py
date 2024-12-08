from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor

class InlineLoading(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.setFixedSize(20, 20)  # Small size for inline display
        
        # Make background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    def start(self):
        """Start the loading animation."""
        self.timer.start(50)
        self.show()
    
    def stop(self):
        """Stop the loading animation."""
        self.timer.stop()
        self.hide()
    
    def rotate(self):
        """Rotate the loading spinner."""
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """Paint the spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw spinner
        painter.translate(self.rect().center())
        painter.rotate(self.angle)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#0084ff"))
        
        # Draw spinning dots
        for i in range(8):
            painter.rotate(45)
            opacity = 0.3 + (i / 8) * 0.7
            painter.setOpacity(opacity)
            painter.drawEllipse(-2, -6, 4, 4)  # Smaller dots 