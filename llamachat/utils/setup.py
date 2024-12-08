import subprocess
import sys
import os
import time
from sqlalchemy import create_engine, text

def check_postgres():
    """Check if PostgreSQL is installed and running."""
    try:
        # Check for psql command
        result = subprocess.run(['which', 'psql'], capture_output=True, text=True)
        if not result.stdout.strip():
            return False
            
        # Check if PostgreSQL is running
        result = subprocess.run(['pg_isready'], capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def install_postgres():
    try:
        print("Starting PostgreSQL installation...")
        
        # Check if Homebrew is installed
        result = subprocess.run(['which', 'brew'], capture_output=True, text=True)
        if not result.stdout.strip():
            print("Installing Homebrew...")
            install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            subprocess.run(install_cmd, shell=True, check=True)

        print("Installing PostgreSQL...")
        subprocess.run(['brew', 'install', 'postgresql@14'], check=True)
        print("Restarting PostgreSQL service...")
        subprocess.run(['brew', 'services', 'restart', 'postgresql@14'], check=True)

        # Wait for PostgreSQL to start and be ready
        print("Waiting for PostgreSQL to start...")
        max_attempts = 30
        for attempt in range(max_attempts):
            result = subprocess.run(['pg_isready'], capture_output=True, text=True)
            if result.returncode == 0:
                print("PostgreSQL is ready!")
                break
            time.sleep(1)
            print(f"Waiting for PostgreSQL... ({attempt + 1}/{max_attempts})")
        else:
            print("PostgreSQL failed to start")
            return False

        # Try connecting to postgres database first
        print("Attempting to connect to postgres database...")
        try:
            subprocess.run(['psql', 'postgres', '-c', r'\l'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error connecting to postgres database: {e}")
            return False

        print("Creating database and user...")
        try:
            # Drop database if exists
            subprocess.run(['dropdb', 'llamachat'], check=False)
            
            # Create database
            subprocess.run(['createdb', 'llamachat'], check=True)
            print("Database 'llamachat' created successfully.")
            
            # Create user
            subprocess.run(['psql', '-d', 'postgres', '-c', 
                          f"CREATE USER postgres WITH PASSWORD 'root' SUPERUSER;"], check=True)
            print("User 'postgres' created successfully.")
            
            # Grant privileges
            subprocess.run(['psql', '-d', 'llamachat', '-c',
                          "GRANT ALL PRIVILEGES ON DATABASE llamachat TO postgres;"], check=True)
            subprocess.run(['psql', '-d', 'llamachat', '-c',
                          "GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;"], check=True)
            print("Privileges granted successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error setting up database: {e}")
            return False

        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during PostgreSQL installation: {e}")
        return False

def setup_database():
    if not check_postgres():
        print("PostgreSQL is not installed. Installing now...")
        if not install_postgres():
            print("Failed to install PostgreSQL. Please install it manually.")
            sys.exit(1)
    
    # Set environment variable for database URL
    os.environ['DATABASE_URL'] = "postgresql://postgres:root@localhost:5432/llamachat"
    
    # Connect to the default 'postgres' database
    engine = create_engine('postgresql://postgres:root@localhost:5432/postgres')

    # Create a new database
    with engine.connect() as connection:
        connection.execute(text("COMMIT"))  # Use text() for raw SQL
        connection.execute(text("CREATE DATABASE llamachat"))

    print("PostgreSQL setup completed successfully!")