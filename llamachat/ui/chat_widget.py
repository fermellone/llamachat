from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListView
from PyQt6.QtCore import pyqtSignal, Qt
import asyncio
import qasync

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

        # Use qasync.asyncSlot() to handle the async call properly
        self.handle_ai_response(messages)

    @qasync.asyncSlot()
    async def handle_ai_response(self, messages):
        # Add temporary message for streaming response
        temp_message = ChatMessage(content="", role="assistant")
        self.chat_model.add_message(temp_message)
        last_index = len(self.chat_model.messages) - 1
        response_content = ""

        try:
            async for chunk in self.ollama_service.get_response(messages):
                response_content += chunk
                # Update the temporary message
                temp_message.content = response_content
                # Notify the view that the item has changed
                model_index = self.chat_model.index(last_index)
                self.chat_model.dataChanged.emit(model_index, model_index)
                self.chat_view.scrollToBottom()
                # Give the event loop a chance to process other events
                await asyncio.sleep(0)

            # Save the complete message to database
            self.db_service.add_message(self.current_chat_id, response_content, "assistant")

        except Exception as e:
            # Handle any errors during generation
            temp_message.content = f"Error generating response: {str(e)}"
            model_index = self.chat_model.index(last_index)
            self.chat_model.dataChanged.emit(model_index, model_index)