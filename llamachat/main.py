from llamachat.ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
from llamachat.database.database import init_db
from llamachat.services.ollama_service import OllamaService
import sys
import qasync
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('llamachat.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Starting LlamaChat")
        # Initialize the database
        init_db()
        
        # Create the Qt application
        app = QApplication(sys.argv)
        
        # Create qasync loop
        logger.debug("Creating event loop")
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        # Create and show the main window
        window = MainWindow()
        window.show()
        
        # Schedule the warmup
        ollama_service = OllamaService()
        loop.create_task(ollama_service.warmup())
        
        # Run the event loop
        logger.info("Starting event loop")
        with loop:
            loop.run_forever()
            
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()