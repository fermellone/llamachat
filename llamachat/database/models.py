from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class Chat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List["Message"] = Relationship(back_populates="chat")

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    role: str  # 'user' or 'assistant'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    chat_id: int = Field(foreign_key="chat.id")
    chat: Chat = Relationship(back_populates="messages")

class Settings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_name: str = Field(default="llama2")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2000) 