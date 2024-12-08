from typing import AsyncGenerator, List, Dict, Optional
from ollama import chat
import asyncio
import threading
import logging
import time
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self, model_name: str = "llama3.2", temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        self._is_warmed_up = False
        self._warmup_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ollama_warmup")
        self._warmup_task: Optional[asyncio.Task] = None

    @property
    def is_warmed_up(self) -> bool:
        """Return whether the model has been warmed up."""
        return self._is_warmed_up

    def _do_warmup(self) -> bool:
        """Execute warmup in a separate thread."""
        try:
            logger.debug(f"Starting warmup in thread: {threading.current_thread().name}")
            # Just initialize the model without streaming
            chat(
                model=self.model_name,
                messages=[{"role": "user", "content": "hi"}],
                stream=False,
                options={"temperature": self.temperature}
            )
            logger.debug("Warmup completed successfully")
            return True
        except Exception as e:
            logger.warning(f"Warmup failed: {str(e)}")
            return False

    async def warmup(self) -> bool:
        """Start warmup in background thread."""
        if self._is_warmed_up:
            return True

        if self._warmup_task is not None:
            # Warmup already in progress
            return await self._warmup_task

        logger.debug("Scheduling warmup")
        try:
            # Run warmup in thread pool
            self._warmup_task = asyncio.create_task(
                asyncio.to_thread(self._do_warmup)
            )
            success = await self._warmup_task
            self._is_warmed_up = success
            return success
        except Exception as e:
            logger.error(f"Error during warmup: {str(e)}")
            self._is_warmed_up = False
            return False
        finally:
            self._warmup_task = None

    async def get_response(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        # If not warmed up, responses might be slower
        if not self._is_warmed_up:
            logger.warning("Model not warmed up, response might be slower")
            
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