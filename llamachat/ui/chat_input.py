from PyQt6.QtWidgets import QWidget, QHBoxLayout, QTextEdit, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt, QEvent

class ChatInput(QWidget):
    message_submitted = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(100)
        self.message_input.setPlaceholderText("Type your message here...")
        
        self.send_button = QPushButton("Send")
        self.setup_send_button()
        
        layout.addWidget(self.message_input)
        layout.addWidget(self.send_button)
        
        self.message_input.installEventFilter(self)
        self.setup_tooltip()
    
    def setup_send_button(self):
        self.send_button.clicked.connect(self.submit_message)
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
    
    def setup_tooltip(self):
        modifier_key = "⌘" if self.is_macos() else "Ctrl"
        self.message_input.setToolTip(
            f"Press Return to send message\n"
            f"Press {modifier_key}+Return to add a new line"
        )
    
    def submit_message(self):
        message = self.message_input.toPlainText().strip()
        if message:
            self.message_submitted.emit(message)
            self.message_input.clear()
    
    def eventFilter(self, source: QWidget, event: QEvent) -> bool:
        if source == self.message_input and event.type() == QEvent.Type.KeyPress:
            # Cast event to QKeyEvent
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
                    self.submit_message()
                    return True
        
        return super().eventFilter(source, event)
    
    @staticmethod
    def is_macos() -> bool:
        import sys
        return sys.platform == 'darwin' 