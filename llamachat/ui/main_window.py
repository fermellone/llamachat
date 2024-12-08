from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QSplitter, QListWidget,
    QListWidgetItem
)
from PyQt6.QtCore import Qt
from llamachat.ui.chat_widget import ChatWidget
from llamachat.services.database_service import DatabaseService

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_service = DatabaseService()
        self.setup_ui()
        self.load_chats()

    def setup_ui(self):
        self.setWindowTitle("Local Chat Assistant")
        self.setMinimumSize(800, 600)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sidebar
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        
        new_chat_btn = QPushButton("New Chat")
        new_chat_btn.clicked.connect(self.create_new_chat)
        new_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #0084ff;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0073e6;
            }
        """)
        
        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.chat_selected)
        
        sidebar_layout.addWidget(new_chat_btn)
        sidebar_layout.addWidget(self.chat_list)
        
        # Chat widget
        self.chat_widget = ChatWidget()
        self.chat_widget.message_sent.connect(self.update_chat_list)
        
        splitter.addWidget(sidebar)
        splitter.addWidget(self.chat_widget)
        splitter.setSizes([200, 600])
        
        layout.addWidget(splitter)

    def load_chats(self):
        self.chat_list.clear()
        chats = self.db_service.get_all_chats()
        for chat in chats:
            item = QListWidgetItem(chat.title)
            item.setData(Qt.ItemDataRole.UserRole, chat.id)
            self.chat_list.addItem(item)

    def create_new_chat(self):
        chat = self.db_service.create_chat()
        item = QListWidgetItem(chat.title)
        item.setData(Qt.ItemDataRole.UserRole, chat.id)
        self.chat_list.insertItem(0, item)
        self.chat_list.setCurrentItem(item)
        self.chat_widget.set_chat(chat.id)

    def chat_selected(self, item):
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        self.chat_widget.set_chat(chat_id)

    def update_chat_list(self, title):
        self.load_chats()