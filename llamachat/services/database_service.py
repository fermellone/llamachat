from typing import List, Optional
from sqlmodel import select
from llamachat.database.models import Chat, Message, Settings
from llamachat.database.database import get_session

class DatabaseService:
    def __init__(self):
        self.session = next(get_session())

    def create_chat(self, title: str = "New Chat") -> Chat:
        chat = Chat(title=title)
        self.session.add(chat)
        self.session.commit()
        self.session.refresh(chat)
        return chat

    def get_all_chats(self) -> List[Chat]:
        statement = select(Chat).order_by(Chat.created_at.desc())
        return self.session.exec(statement).all()

    def get_chat(self, chat_id: int) -> Optional[Chat]:
        statement = select(Chat).where(Chat.id == chat_id)
        return self.session.exec(statement).first()

    def add_message(self, chat_id: int, content: str, role: str) -> Message:
        message = Message(content=content, role=role, chat_id=chat_id)
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message

    def get_chat_messages(self, chat_id: int) -> List[Message]:
        statement = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
        return self.session.exec(statement).all()

    def get_settings(self) -> Settings:
        statement = select(Settings)
        settings = self.session.exec(statement).first()
        if not settings:
            settings = Settings()
            self.session.add(settings)
            self.session.commit()
            self.session.refresh(settings)
        return settings 

    def delete_chat(self, chat_id: int) -> bool:
        try:
            # First delete all messages associated with the chat
            statement = select(Message).where(Message.chat_id == chat_id)
            messages = self.session.exec(statement).all()
            for message in messages:
                self.session.delete(message)
            
            # Then delete the chat itself
            chat = self.get_chat(chat_id)
            if chat:
                self.session.delete(chat)
                self.session.commit()
                return True
            return False
        except Exception as e:
            print(f"Error deleting chat: {e}")
            self.session.rollback()
            return False

    def rename_chat(self, chat_id: int, new_title: str) -> bool:
        try:
            chat = self.get_chat(chat_id)
            if chat:
                chat.title = new_title
                self.session.commit()
                return True
            return False
        except Exception as e:
            print(f"Error renaming chat: {e}")
            self.session.rollback()
            return False