from llamachat.ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
from llamachat.database.database import init_db
import sys

def main():
    # Initialize the database
    init_db()
    
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 