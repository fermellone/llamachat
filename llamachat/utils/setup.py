import os
from sqlmodel import create_engine, text

def setup_database():
    """Setup SQLite database."""
    try:
        # Get database path from URL
        db_path = os.path.expanduser('~') + '/Library/Application Support/LlamaChat/llamachat.db'
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create engine
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Test connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            print("Database connection successful!")
            
    except Exception as e:
        print(f"Error setting up database: {e}")
        raise