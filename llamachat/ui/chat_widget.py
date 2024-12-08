from dataclasses import dataclass
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, 
    QPushButton, QHBoxLayout, QListView,
    QStyledItemDelegate
)
from PyQt6.QtCore import pyqtSignal, Qt, QEvent, QAbstractListModel, QModelIndex, QRect, QSize, QRectF
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QFont, QFontMetrics
from llamachat.services.database_service import DatabaseService
from llamachat.services.ollama_service import OllamaService
import asyncio

from bs4 import BeautifulSoup  # Ensure BeautifulSoup is installed

@dataclass
class ChatMessage:
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class ChatModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.messages = []
    
    def data(self, index: QModelIndex, role: int):
        if not index.isValid():
            return None
            
        if role == Qt.ItemDataRole.DisplayRole:
            return self.messages[index.row()]
            
        return None
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.messages)
    
    def add_message(self, message: ChatMessage):
        self.beginInsertRows(QModelIndex(), len(self.messages), len(self.messages))
        self.messages.append(message)
        self.endInsertRows()

class ChatDelegate(QStyledItemDelegate):
    PADDING = 10
    BUBBLE_RADIUS = 15
    MIN_WIDTH = 200  # Minimum bubble width
    WIDTH_RATIO = 0.7  # Maximum bubble width as a ratio of view width
    
    def __init__(self):
        super().__init__()
        self.font = QFont("SF Pro", 12)
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

class ChatWidget(QWidget):
    message_sent = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.db_service = DatabaseService()
        self.ollama_service = OllamaService()
        self.current_chat_id = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Chat display area
        self.chat_view = QListView()
        self.chat_model = ChatModel()
        self.chat_delegate = ChatDelegate()
        self.chat_view.setModel(self.chat_model)
        self.chat_view.setItemDelegate(self.chat_delegate)
        self.chat_view.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.chat_view.setSpacing(10)
        
        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(100)
        self.message_input.setPlaceholderText("Type your message here...")
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #0084ff;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0073e6;
            }
        """)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        
        layout.addWidget(self.chat_view)
        layout.addLayout(input_layout)
        
        # Connect message input events
        self.message_input.installEventFilter(self)
        
        # Add tooltip for message input
        modifier_key = "⌘" if self.is_macos() else "Ctrl"
        self.message_input.setToolTip(
            f"Press Return to send message\n"
            f"Press {modifier_key}+Return to add a new line"
        )

    def set_chat(self, chat_id: int):
        self.current_chat_id = chat_id
        self.load_chat_history()

    def load_chat_history(self):
        if self.current_chat_id is None:
            return
        
        # Clear existing messages
        self.chat_model.messages.clear()
        self.chat_model.layoutChanged.emit()
        
        # Load messages from database
        messages = self.db_service.get_chat_messages(self.current_chat_id)
        for msg in messages:
            chat_message = ChatMessage(content=msg.content, role=msg.role)
            self.chat_model.add_message(chat_message)
        
        # Scroll to bottom
        self.chat_view.scrollToBottom()

    def send_message(self):
        if self.current_chat_id is None:
            chat = self.db_service.create_chat()
            self.current_chat_id = chat.id
            self.message_sent.emit(chat.title)

        message = self.message_input.toPlainText().strip()
        if not message:
            return

        # Save and display user message
        self.db_service.add_message(self.current_chat_id, message, "user")
        self.chat_model.add_message(ChatMessage(content=message, role="user"))
        self.message_input.clear()

        # Get chat history
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in self.db_service.get_chat_messages(self.current_chat_id)
        ]

        # Process AI response asynchronously
        loop = asyncio.get_event_loop()
        loop.create_task(self.handle_ai_response(messages))

    async def handle_ai_response(self, messages):
        response_content = await self.process_ollama_response(messages)
        self.db_service.add_message(self.current_chat_id, response_content, "assistant")
        
        # Add assistant message to the view
        self.chat_model.add_message(ChatMessage(content=response_content, role="assistant"))
        self.chat_view.scrollToBottom()

    async def process_ollama_response(self, messages):
        response_content = ""
        
        # Add temporary message for streaming response
        temp_message = ChatMessage(content="", role="assistant")
        self.chat_model.add_message(temp_message)
        last_index = len(self.chat_model.messages) - 1

        async for chunk in self.ollama_service.get_response(messages):
            response_content += chunk
            # Update the temporary message
            temp_message.content = response_content
            # Notify the view that the item has changed
            model_index = self.chat_model.index(last_index)
            self.chat_model.dataChanged.emit(model_index, model_index)
            self.chat_view.scrollToBottom()
        
        return response_content

    def clear_chat(self):
        self.current_chat_id = None
        self.chat_model.messages.clear()
        self.chat_model.layoutChanged.emit()
        self.message_input.clear()

    def eventFilter(self, source: QWidget, event: QEvent) -> bool:
        if source == self.message_input and event.type() == QEvent.Type.KeyPress:
            # Cast event to QKeyEvent instead of creating a new one
            key_event = event
            
            # Check for platform-specific modifier keys
            modifier = Qt.KeyboardModifier.MetaModifier if self.is_macos() else Qt.KeyboardModifier.ControlModifier
            
            # Handle Return/Enter key
            if key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # If modifier (Cmd/Ctrl) is pressed, insert newline
                if key_event.modifiers() & modifier:
                    self.message_input.insertPlainText('\n')
                    return True
                # If no modifier, send message
                elif not key_event.modifiers():
                    self.send_message()
                    return True
        
        return super().eventFilter(source, event)

    def is_macos(self) -> bool:
        import sys
        return sys.platform == 'darwin'