from dataclasses import dataclass
from typing import Optional
import os
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    model_name: str = "llama3.2"
    temperature: float = 0.7
    max_retries: int = 3
    database_url: str = "postgresql://postgres:postgres@localhost:5432/llamachat"
    log_level: str = "INFO"
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'AppConfig':
        """Load configuration from file or environment."""
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                config_dict = json.load(f)
                return cls(**config_dict)
        
        return cls(
            model_name=os.getenv("LLAMA_MODEL", cls.model_name),
            temperature=float(os.getenv("LLAMA_TEMPERATURE", cls.temperature)),
            max_retries=int(os.getenv("LLAMA_MAX_RETRIES", cls.max_retries)),
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            log_level=os.getenv("LOG_LEVEL", cls.log_level)
        ) 