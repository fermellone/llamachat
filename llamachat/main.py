import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import logging
import qasync
import asyncio
from PyQt6.QtWidgets import QApplication
from llamachat.ui.main_window import MainWindow
from llamachat.database.database import init_db
from llamachat.utils.setup import setup_database
from llamachat.config import AppConfig

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def setup_logging(config: AppConfig):
    """Setup application logging."""
    # Get user's home directory
    home = os.path.expanduser("~")
    log_path = os.path.join(home, 'Library', 'Logs', 'LlamaChat', 'llamachat.log')
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path)
        ]
    )

def main():
    try:
        # Load configuration
        try:
            config = AppConfig.load()
        except Exception as e:
            print(f"Failed to load config: {e}")
            raise
        
        # Setup logging
        setup_logging(config)
        logger = logging.getLogger(__name__)
        logger.info("Starting LlamaChat")
        
        # Log important paths
        logger.info(f"Working Directory: {os.getcwd()}")
        logger.info(f"Resource Path: {resource_path('.')}")
        logger.info(f"Sys Path: {sys.path}")
        
        # Setup database
        try:
            setup_database()
            logger.info("Database setup completed")
        except Exception as e:
            logger.error(f"Database setup failed: {e}", exc_info=True)
            raise
        
        try:
            # Initialize database schema
            init_db()
            logger.info("Database initialization completed")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            raise
        
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Create event loop
        try:
            loop = qasync.QEventLoop(app)
            asyncio.set_event_loop(loop)
            logger.info("Event loop setup completed")
        except Exception as e:
            logger.error(f"Event loop setup failed: {e}", exc_info=True)
            raise
        
        # Create main window
        try:
            window = MainWindow()
            window.show()
            logger.info("Main window created and shown")
        except Exception as e:
            logger.error(f"Failed to create/show main window: {e}", exc_info=True)
            raise
        
        # Run event loop
        with loop:
            loop.run_forever()
            
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error", exc_info=True)
        if not logging.getLogger().handlers:  # If logging isn't set up yet
            print(f"Fatal error: {e}")  # Print to console
        sys.exit(1)

if __name__ == "__main__":
    main()
