import asyncio
from typing import AsyncGenerator, List, Dict
from ollama import chat

class OllamaService:
    def __init__(self, model_name: str = "llama3.2", temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature

    async def get_response(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        response = chat(
            model=self.model_name,
            messages=messages,
            stream=True,
            options={
                "temperature": self.temperature
            }
        )

        for chunk in response:
            yield chunk.message.content 