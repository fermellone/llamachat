from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QSplitter, QListWidget,
    QListWidgetItem, QMessageBox, QMenu,
    QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from llamachat.ui.chat_widget import ChatWidget
from llamachat.services.database_service import DatabaseService
from llamachat.ui.widgets.overlay_loading import OverlayLoading
from llamachat.services.ollama_service import OllamaService
import qasync

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_services()
        
        # Create loading overlay before UI setup
        self.loading = OverlayLoading("Initializing application...", self)
        self.loading.start()
        
        self.setup_ui()
        self.setup_connections()
        self.initialize_app()

    def setup_services(self):
        """Initialize all services."""
        self.db_service = DatabaseService()
        self.ollama_service = OllamaService()

    def setup_connections(self):
        """Setup all signal connections."""
        self.chat_widget.message_sent.connect(self.update_chat_list)
        self.chat_widget.error_occurred.connect(self.show_error_dialog)
        
    def show_error_dialog(self, message: str):
        """Show error dialog to user."""
        QMessageBox.critical(
            self,
            "Error",
            message,
            QMessageBox.StandardButton.Ok
        )

    @qasync.asyncSlot()
    async def initialize_app(self):
        """Initialize the application asynchronously."""
        self.loading.setText("Initializing application...")
        try:
            # Load chats
            self.load_chats()
            
            # Warm up Ollama
            self.loading.setText("Warming up AI model...")
            success = await self.ollama_service.warmup()
            
            if not success:
                QMessageBox.warning(
                    self,
                    "Warmup Warning",
                    "AI model warmup failed. The first response might be slower than usual."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Error during initialization: {str(e)}"
            )
        finally:
            self.loading.stop()

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
        
        # Add context menu to chat list
        self.chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self.show_context_menu)

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

    def show_context_menu(self, position):
        item = self.chat_list.itemAt(position)
        if item is None:
            return

        menu = QMenu()
        rename_action = menu.addAction("Rename Chat")
        delete_action = menu.addAction("Delete Chat")
        
        action = menu.exec(self.chat_list.mapToGlobal(position))
        
        if action == delete_action:
            self.confirm_delete_chat(item)
        elif action == rename_action:
            self.rename_chat(item)

    def confirm_delete_chat(self, item):
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        
        # Show confirmation dialog
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText("Are you sure you want to delete this chat?")
        msg_box.setInformativeText("This action cannot be undone.")
        msg_box.setWindowTitle("Confirm Delete")
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            if self.db_service.delete_chat(chat_id):
                row = self.chat_list.row(item)
                self.chat_list.takeItem(row)
                # Clear the chat widget if the deleted chat was selected
                if self.chat_widget.current_chat_id == chat_id:
                    self.chat_widget.clear_chat()

    def rename_chat(self, item):
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        current_title = item.text()
        
        new_title, ok = QInputDialog.getText(
            self,
            "Rename Chat",
            "Enter new chat name:",
            text=current_title
        )
        
        if ok and new_title.strip():
            if self.db_service.rename_chat(chat_id, new_title):
                item.setText(new_title)