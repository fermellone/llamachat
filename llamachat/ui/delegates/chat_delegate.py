from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import Qt, QRect, QSize, QRectF
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QFont, QFontMetrics
from llamachat.ui.models.chat_message import ChatMessage

class ChatDelegate(QStyledItemDelegate):
    PADDING = 10
    BUBBLE_RADIUS = 15
    MIN_WIDTH = 200
    WIDTH_RATIO = 0.7
    
    def __init__(self):
        super().__init__()
        self.font = QFont()
        self.font.setPointSize(12)
        self.metrics = QFontMetrics(self.font)
    
    def paint(self, painter: QPainter, option, index):
        message: ChatMessage = index.data()
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font)
        
        # Calculate maximum width based on view width
        view_width = option.widget.width() if option.widget else 800
        max_width = max(self.MIN_WIDTH, int(view_width * self.WIDTH_RATIO))
        
        # Calculate text dimensions
        text_width = min(self.metrics.horizontalAdvance(message.content) + 2 * self.PADDING, 
                        max_width)
        text_height = self.metrics.boundingRect(
            QRect(0, 0, text_width - 2 * self.PADDING, 0),
            Qt.TextFlag.TextWordWrap,
            message.content
        ).height() + 2 * self.PADDING
        
        # Calculate bubble dimensions and position
        bubble_width = text_width
        bubble_height = text_height
        
        if message.role == "user":
            bubble_x = min(option.rect.right() - bubble_width - self.PADDING,
                         view_width - bubble_width - self.PADDING * 2)
            bubble_color = QColor("#DCF8C6")
        else:
            bubble_x = self.PADDING
            bubble_color = QColor("#FFFFFF")
        
        # Convert QRect to QRectF for the bubble
        bubble_rect = QRectF(
            bubble_x,
            option.rect.top() + self.PADDING,
            bubble_width,
            bubble_height
        )
        
        # Draw bubble
        path = QPainterPath()
        path.addRoundedRect(bubble_rect, self.BUBBLE_RADIUS, self.BUBBLE_RADIUS)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bubble_color)
        painter.drawPath(path)
        
        # Draw text
        text_rect = QRect(
            int(bubble_rect.x() + self.PADDING),
            int(bubble_rect.y() + self.PADDING),
            int(bubble_rect.width() - 2 * self.PADDING),
            int(bubble_rect.height() - 2 * self.PADDING)
        )
        painter.setPen(QColor("#000000"))
        painter.drawText(text_rect, Qt.TextFlag.TextWordWrap, message.content)
    
    def sizeHint(self, option, index):
        message: ChatMessage = index.data()
        
        # Calculate maximum width based on view width
        view_width = option.widget.width() if option.widget else 800
        max_width = max(self.MIN_WIDTH, int(view_width * self.WIDTH_RATIO))
        
        # Calculate text dimensions
        text_width = min(self.metrics.horizontalAdvance(message.content) + 2 * self.PADDING,
                        max_width)
        text_height = self.metrics.boundingRect(
            QRect(0, 0, text_width - 2 * self.PADDING, 0),
            Qt.TextFlag.TextWordWrap,
            message.content
        ).height() + 2 * self.PADDING
        
        return QSize(view_width, text_height + 2 * self.PADDING)
    
    # ... rest of the ChatDelegate implementation ... 