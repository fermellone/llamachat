from llamachat.ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
from llamachat.database.database import init_db
import sys
import qasync
import asyncio

def main():
    # Initialize the database
    init_db()
    
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Create the qasync loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Run the event loop
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)