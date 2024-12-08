from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListView
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
from .widgets.inline_loading import InlineLoading

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
        
        # Create inline loading indicator
        self.loading = InlineLoading(self)
        self.loading.hide()
        
        self.scroll_start = 0
        self.scroll_start_time = 0
        self.scroll_duration = 0.3
        
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
        
        # Position loading indicator at the bottom
        self.loading.move(
            self.chat_input.x() + 10,  # 10px margin from left
            self.chat_input.y() - 25    # 25px above chat input
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
        scrollbar = self.chat_view.verticalScrollBar()
        if not self.scroll_timer.isActive():
            self.scroll_timer.start(16)  # ~60 FPS for smoother animation
            self.scroll_start = scrollbar.value()
            self.scroll_target = scrollbar.maximum()
            self.scroll_start_time = time.time()
            self.scroll_duration = 0.3  # 300ms animation

    def _perform_scroll(self):
        """Perform smooth scroll animation using easing."""
        scrollbar = self.chat_view.verticalScrollBar()
        current_time = time.time()
        elapsed = current_time - self.scroll_start_time
        
        if elapsed < self.scroll_duration:
            # Easing function (ease-out cubic)
            progress = elapsed / self.scroll_duration
            t = 1 - (1 - progress) ** 3
            
            # Calculate new position
            new_value = self.scroll_start + (self.scroll_target - self.scroll_start) * t
            scrollbar.setValue(int(new_value))
            
            # Continue animation
            self.scroll_timer.start(16)
        else:
            # Ensure we reach the exact target
            scrollbar.setValue(self.scroll_target)

    def set_chat(self, chat_id: int):
        """Set the current chat and load its history."""
        self.current_chat_id = chat_id
        self.load_chat_history()

    def load_chat_history(self):
        """Load chat history from database."""
        if self.current_chat_id is None:
            return
        
        # Start loading indicator without text
        self.loading.start()
        
        # Clear existing messages
        self.chat_model.clear()
        
        # Load messages from database
        messages = self.db_service.get_chat_messages(self.current_chat_id)
        for msg in messages:
            chat_message = ChatMessage(content=msg.content, role=msg.role)
            self.chat_model.add_message(chat_message)
        
        self.loading.stop()
        
        # Schedule scroll after the view has been updated
        QTimer.singleShot(100, self.delayed_scroll_to_bottom)

    def delayed_scroll_to_bottom(self):
        """Scroll to bottom after the view has been updated."""
        scrollbar = self.chat_view.verticalScrollBar()
        if scrollbar.maximum() > 0:  # Only scroll if there's content
            self.smooth_scroll_to_bottom()
        else:  # If content not ready yet, try again
            QTimer.singleShot(50, self.delayed_scroll_to_bottom)

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
        # Show loading indicator
        self.loading.start()
        
        start_time = time.time()
        logger.debug(f"handle_ai_response started in thread: {threading.current_thread().name}")
        
        # Add temporary message with loading indicator
        temp_message = ChatMessage(content="", role="assistant")  # Empty content initially
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
        # Update loading indicator position when window resizes
        if self.loading:
            self.loading.move(
                self.chat_input.x() + 10,
                self.chat_input.y() - 25
            )

    def clear_chat(self):
        """Clear the current chat and reset state."""
        self.current_chat_id = None
        self.chat_model.clear()
        
        # Stop any ongoing loading
        if self.loading and self.loading.isVisible():
            self.loading.stop()