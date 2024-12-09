from PyQt6.QtCore import QAbstractListModel, Qt, QModelIndex
from llamachat.ui.models.chat_message import ChatMessage

class ChatListModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.messages = []
    
    def data(self, index: QModelIndex, role: int):
        if not index.isValid():
            return None
            
        if role == Qt.ItemDataRole.DisplayRole:
            return self.messages[index.row()]
            
        return None
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.messages)
    
    def add_message(self, message: ChatMessage):
        self.beginInsertRows(QModelIndex(), len(self.messages), len(self.messages))
        self.messages.append(message)
        self.endInsertRows()

    def clear(self):
        self.messages.clear()
        self.layoutChanged.emit() 