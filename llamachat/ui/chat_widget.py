from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, 
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt

class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        
        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(100)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        
        layout.addWidget(self.chat_display)
        layout.addLayout(input_layout)
    
    def send_message(self):
        # TODO: Implement message sending
        message = self.message_input.toPlainText()
        if message.strip():
            self.chat_display.append(f"You: {message}")
            self.message_input.clear()
            # TODO: Send to Ollama and handle response 