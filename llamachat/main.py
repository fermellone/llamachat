from llamachat.config import AppConfig
import sys
import logging
import qasync
import asyncio
from PyQt6.QtWidgets import QApplication
from .ui.main_window import MainWindow
from .database.database import init_db

def setup_logging(config: AppConfig):
    """Setup application logging."""
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('llamachat.log')
        ]
    )

def main():
    try:
        # Load configuration
        config = AppConfig.load()
        
        # Setup logging
        setup_logging(config)
        logger = logging.getLogger(__name__)
        logger.info("Starting LlamaChat")
        
        # Initialize database
        init_db()
        
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Create event loop
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # Create main window
        window = MainWindow()
        window.show()
        
        # Run event loop
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