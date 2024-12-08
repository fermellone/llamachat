from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter, QColor

class OverlayLoading(QWidget):
    def __init__(self, text="Loading...", parent=None):
        super().__init__(parent)
        
        # Make the widget fill the parent
        self.setParent(parent)
        
        # Enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Setup animation
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 14px;
                background-color: transparent;
                padding: 10px;
            }
        """)
        
        layout.addWidget(self.label)
    
    def setText(self, text: str):
        """Update the loading text."""
        self.label.setText(text)
    
    def start(self):
        """Start the loading animation and show the overlay."""
        if self.parent():
            self.resize(self.parent().size())
        self.timer.start(50)
        self.show()
        self.raise_()  # Ensure overlay is on top
    
    def stop(self):
        """Stop the loading animation and hide the overlay."""
        self.timer.stop()
        self.hide()
    
    def rotate(self):
        """Rotate the loading spinner."""
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def resizeEvent(self, event):
        """Handle parent widget resize."""
        if self.parent():
            self.resize(self.parent().size())
    
    def paintEvent(self, event):
        """Paint the overlay and loading spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw semi-transparent background
        painter.fillRect(self.rect(), QColor(255, 255, 255, 200))
        
        # Draw spinner
        center = self.rect().center()
        painter.translate(center)
        painter.rotate(self.angle)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#0084ff"))
        
        # Draw spinning dots
        for i in range(8):
            painter.rotate(45)
            opacity = 0.3 + (i / 8) * 0.7
            painter.setOpacity(opacity)
            painter.drawEllipse(-5, -20, 10, 10) 