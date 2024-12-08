from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListView
from PyQt6.QtCore import pyqtSignal, Qt
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

class ChatWidget(QWidget):
    message_sent = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.db_service = DatabaseService()
        self.ollama_service = OllamaService()
        self.current_chat_id = None
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

    def setup_chat_view(self):
        self.chat_view.setModel(self.chat_model)
        self.chat_view.setItemDelegate(self.chat_delegate)
        self.chat_view.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.chat_view.setSpacing(10)

    def set_chat(self, chat_id: int):
        """Set the current chat and load its history."""
        self.current_chat_id = chat_id
        self.load_chat_history()

    def load_chat_history(self):
        """Load chat history from database."""
        if self.current_chat_id is None:
            return
        
        # Clear existing messages
        self.chat_model.clear()
        
        # Load messages from database
        messages = self.db_service.get_chat_messages(self.current_chat_id)
        for msg in messages:
            chat_message = ChatMessage(content=msg.content, role=msg.role)
            self.chat_model.add_message(chat_message)
        
        # Scroll to bottom
        self.chat_view.scrollToBottom()

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
        start_time = time.time()
        logger.debug(f"handle_ai_response started in thread: {threading.current_thread().name}")
        
        # Add temporary message with loading indicator
        temp_message = ChatMessage(content="Generating response...", role="assistant")
        self.chat_model.add_message(temp_message)
        last_index = len(self.chat_model.messages) - 1
        response_content = ""
        chunk_count = 0

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
                    
                    if chunk_count % 30 == 0:  # Log every 30 chunks
                        logger.debug(
                            f"Processing chunk {chunk_count} in thread: {threading.current_thread().name}, "
                            f"content length: {len(response_content)}, "
                            f"time elapsed: {time.time() - start_time:.2f}s"
                        )
                    
                    # Scroll and yield to event loop less frequently
                    if chunk_count % 10 == 0:
                        self.chat_view.scrollToBottom()
                        await asyncio.sleep(0.01)

            # Final update with complete response
            temp_message.content = response_content
            model_index = self.chat_model.index(last_index)
            self.chat_model.dataChanged.emit(model_index, model_index)
            self.chat_view.scrollToBottom()

            logger.debug(f"Stream completed in {time.time() - start_time:.2f}s, saving to database")
            await asyncio.to_thread(
                self.db_service.add_message,
                self.current_chat_id,
                response_content,
                "assistant"
            )

        except Exception as e:
            logger.error(f"Error in handle_ai_response: {str(e)}", exc_info=True)
            temp_message.content = f"Error generating response: {str(e)}"
            model_index = self.chat_model.index(last_index)
            self.chat_model.dataChanged.emit(model_index, model_index)