from typing import AsyncGenerator, List, Dict
from ollama import chat
import asyncio
import threading
import logging
import time

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self, model_name: str = "llama3.2", temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature

    async def get_response(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        start_time = time.time()
        logger.debug(f"Starting get_response in thread: {threading.current_thread().name}")
        
        # Define the blocking chat operation
        def execute_chat():
            logger.debug(f"Executing chat in thread: {threading.current_thread().name}")
            return chat(
                model=self.model_name,
                messages=messages,
                stream=True,
                options={"temperature": self.temperature}
            )

        try:
            # Run the blocking operation in a separate thread
            response = await asyncio.to_thread(execute_chat)
            logger.debug(f"ollama.chat completed in {time.time() - start_time:.2f}s, starting stream")

            chunk_count = 0
            stream_start = time.time()
            async for chunk in self._process_stream(response):
                chunk_count += 1
                if chunk_count % 10 == 0:  # Log every 10th chunk to avoid spam
                    logger.debug(
                        f"Streaming chunk {chunk_count} in thread: {threading.current_thread().name}, "
                        f"time since start: {time.time() - stream_start:.2f}s"
                    )
                yield chunk

        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}", exc_info=True)
            raise

    async def _process_stream(self, response):
        """Process the stream in chunks asynchronously."""
        for chunk in response:
            # Give other tasks a chance to run
            await asyncio.sleep(0)
            yield chunk.message.content

    async def warmup(self):
        """Perform a warmup request to reduce cold-start latency."""
        logger.debug("Performing warmup request")
        warmup_messages = [{"role": "user", "content": "hi"}]
        try:
            async for _ in self.get_response(warmup_messages):
                break  # We only need the first chunk
            logger.debug("Warmup completed successfully")
        except Exception as e:
            logger.warning(f"Warmup request failed: {str(e)}")