from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListView, QScrollBar
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
import asyncio
import qasync
import threading
import logging
import time

logger = logging.getLogger(__name__)

from .models.chat_message import ChatMessage
from .models.chat_list_model import ChatListModel
from .delegates.chat_delegate import ChatDelegate
from .chat_input import ChatInput
from ..services.database_service import DatabaseService
from ..services.ollama_service import OllamaService
from .widgets.loading_indicator import LoadingIndicator

class ChatWidget(QWidget):
    message_sent = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.db_service = DatabaseService()
        self.ollama_service = OllamaService()
        self.current_chat_id = None
        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self._perform_scroll)
        self.loading = LoadingIndicator("", self)
        self.loading.hide()
        self.setup_ui()
        logger.debug(f"ChatWidget initialized in thread: {threading.current_thread().name}")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Chat display
        self.chat_view = QListView()
        self.chat_model = ChatListModel()
        self.chat_delegate = ChatDelegate()
        self.setup_chat_view()
        
        # Chat input
        self.chat_input = ChatInput()
        self.chat_input.message_submitted.connect(self.send_message)
        
        layout.addWidget(self.chat_view)
        layout.addWidget(self.chat_input)
        
        # Position loading indicator in center
        self.loading.setParent(self)
        self.loading.move(
            (self.width() - self.loading.width()) // 2,
            (self.height() - self.loading.height()) // 2
        )

    def setup_chat_view(self):
        self.chat_view.setModel(self.chat_model)
        self.chat_view.setItemDelegate(self.chat_delegate)
        self.chat_view.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.chat_view.setSpacing(10)
        self.chat_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # Enable smooth scrolling
        scrollbar = self.chat_view.verticalScrollBar()
        scrollbar.setSingleStep(10)
        scrollbar.setPageStep(self.chat_view.height())

    def smooth_scroll_to_bottom(self):
        """Schedule a smooth scroll to bottom."""
        if not self.scroll_timer.isActive():
            self.scroll_timer.start(10)  # 10ms delay

    def _perform_scroll(self):
        """Actually perform the scroll operation."""
        scrollbar = self.chat_view.verticalScrollBar()
        current = scrollbar.value()
        maximum = scrollbar.maximum()
        
        if current < maximum:
            # Smooth scroll animation
            step = (maximum - current) // 4  # Adjust divisor to control speed
            new_value = min(current + step, maximum)
            scrollbar.setValue(new_value)
            
            # Continue scrolling if not at bottom
            if new_value < maximum:
                self.scroll_timer.start(10)

    def set_chat(self, chat_id: int):
        """Set the current chat and load its history."""
        self.current_chat_id = chat_id
        self.load_chat_history()

    def load_chat_history(self):
        """Load chat history from database."""
        if self.current_chat_id is None:
            return
        
        self.loading.setText("Loading chat history...")
        self.loading.start()
        
        # Clear existing messages
        self.chat_model.clear()
        
        # Load messages from database
        messages = self.db_service.get_chat_messages(self.current_chat_id)
        for msg in messages:
            chat_message = ChatMessage(content=msg.content, role=msg.role)
            self.chat_model.add_message(chat_message)
        
        self.loading.stop()
        self.smooth_scroll_to_bottom()

    def send_message(self, message: str):
        logger.debug(f"send_message called in thread: {threading.current_thread().name}")
        if self.current_chat_id is None:
            chat = self.db_service.create_chat()
            self.current_chat_id = chat.id
            self.message_sent.emit(chat.title)

        # Save and display user message
        self.db_service.add_message(self.current_chat_id, message, "user")
        self.chat_model.add_message(ChatMessage(content=message, role="user"))

        # Get chat history
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in self.db_service.get_chat_messages(self.current_chat_id)
        ]

        logger.debug("Calling handle_ai_response")
        self.handle_ai_response(messages)

    @qasync.asyncSlot()
    async def handle_ai_response(self, messages):
        self.loading.setText("Generating response...")
        self.loading.start()
        
        start_time = time.time()
        logger.debug(f"handle_ai_response started in thread: {threading.current_thread().name}")
        
        # Add temporary message with loading indicator
        temp_message = ChatMessage(content="Generating response...", role="assistant")
        self.chat_model.add_message(temp_message)
        last_index = len(self.chat_model.messages) - 1
        response_content = ""
        chunk_count = 0
        last_scroll_time = 0
        scroll_interval = 0.1  # seconds

        try:
            logger.debug("Starting to process AI response stream")
            async for chunk in self.ollama_service.get_response(messages):
                chunk_count += 1
                response_content += chunk
                
                # Update UI less frequently to reduce overhead
                if chunk_count % 3 == 0:  # Update every 3 chunks
                    temp_message.content = response_content
                    model_index = self.chat_model.index(last_index)
                    self.chat_model.dataChanged.emit(model_index, model_index)
                    
                    # Log every 30 chunks
                    if chunk_count % 30 == 0:
                        logger.debug(
                            f"Processing chunk {chunk_count} in thread: {threading.current_thread().name}, "
                            f"content length: {len(response_content)}, "
                            f"time elapsed: {time.time() - start_time:.2f}s"
                        )
                    
                    # Smooth scrolling with rate limiting
                    current_time = time.time()
                    if current_time - last_scroll_time >= scroll_interval:
                        self.smooth_scroll_to_bottom()
                        last_scroll_time = current_time
                        await asyncio.sleep(0.01)

            # Final update with complete response
            temp_message.content = response_content
            model_index = self.chat_model.index(last_index)
            self.chat_model.dataChanged.emit(model_index, model_index)
            self.smooth_scroll_to_bottom()

            logger.debug(f"Stream completed in {time.time() - start_time:.2f}s, saving to database")
            await asyncio.to_thread(
                self.db_service.add_message,
                self.current_chat_id,
                response_content,
                "assistant"
            )

            self.loading.stop()
        except Exception as e:
            self.loading.stop()
            logger.error(f"Error in handle_ai_response: {str(e)}", exc_info=True)
            temp_message.content = f"Error generating response: {str(e)}"
            model_index = self.chat_model.index(last_index)
            self.chat_model.dataChanged.emit(model_index, model_index)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.loading:
            self.loading.move(
                (self.width() - self.loading.width()) // 2,
                (self.height() - self.loading.height()) // 2
            )