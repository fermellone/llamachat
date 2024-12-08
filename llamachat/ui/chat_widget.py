from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, 
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
import markdown
from llamachat.services.database_service import DatabaseService
from llamachat.services.ollama_service import OllamaService
import asyncio
from functools import partial

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
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 10px;
            }
        """)
        
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
        
        layout.addWidget(self.chat_display)
        layout.addLayout(input_layout)

    def set_chat(self, chat_id: int):
        self.current_chat_id = chat_id
        self.load_chat_history()

    def load_chat_history(self):
        if self.current_chat_id is None:
            return
        
        messages = self.db_service.get_chat_messages(self.current_chat_id)
        self.chat_display.clear()
        
        for message in messages:
            self.display_message(message.content, message.role)

    def display_message(self, content: str, role: str):
        html_content = markdown.markdown(content)
        role_style = "color: #0084ff;" if role == "assistant" else "color: #000000;"
        role_name = "Assistant" if role == "assistant" else "You"
        
        message_html = f"""
            <div style='margin-bottom: 10px;'>
                <strong style='{role_style}'>{role_name}:</strong>
                <div style='margin-left: 20px; color: #000000;'>{html_content}</div>
            </div>
        """
        self.chat_display.append(message_html)

    async def process_ollama_response(self, messages):
        response_content = ""
        async for chunk in self.ollama_service.get_response(messages):
            response_content += chunk
        # Display the complete response once
        self.display_message(response_content, "assistant")
        return response_content

    def send_message(self):
        if self.current_chat_id is None:
            # Create new chat if none exists
            chat = self.db_service.create_chat()
            self.current_chat_id = chat.id
            self.message_sent.emit(chat.title)

        message = self.message_input.toPlainText().strip()
        if not message:
            return

        # Save and display user message
        self.db_service.add_message(self.current_chat_id, message, "user")
        self.display_message(message, "user")
        self.message_input.clear()

        # Get chat history
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in self.db_service.get_chat_messages(self.current_chat_id)
        ]

        # Process AI response asynchronously using qasync
        loop = asyncio.get_event_loop()
        loop.create_task(self.handle_ai_response(messages))

    async def handle_ai_response(self, messages):
        response_content = await self.process_ollama_response(messages)
        # Save AI response to database
        self.db_service.add_message(self.current_chat_id, response_content, "assistant")

    def clear_chat(self):
        self.current_chat_id = None
        self.chat_display.clear()
        self.message_input.clear()