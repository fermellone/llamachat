from dataclasses import dataclass
from datetime import datetime

@dataclass
class ChatMessage:
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now() 