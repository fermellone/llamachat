from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QSplitter, QListWidget
)
from PyQt6.QtCore import Qt
from .chat_widget import ChatWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local Chat Assistant")
        self.setMinimumSize(800, 600)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create splitter for sidebar and chat
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sidebar with chat list
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        
        # Chat list
        self.chat_list = QListWidget()
        new_chat_btn = QPushButton("New Chat")
        new_chat_btn.clicked.connect(self.create_new_chat)
        
        sidebar_layout.addWidget(new_chat_btn)
        sidebar_layout.addWidget(self.chat_list)
        
        # Chat widget
        self.chat_widget = ChatWidget()
        
        # Add widgets to splitter
        splitter.addWidget(sidebar)
        splitter.addWidget(self.chat_widget)
        
        # Set initial sizes for splitter
        splitter.setSizes([200, 600])
        
        layout.addWidget(splitter)
    
    def create_new_chat(self):
        # TODO: Implement new chat creation
        pass 