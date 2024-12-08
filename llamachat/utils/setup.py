import subprocess
import sys
import os

def check_postgres():
    try:
        result = subprocess.run(['which', 'postgres'], capture_output=True, text=True)
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False

def install_postgres():
    try:
        # Check if Homebrew is installed
        result = subprocess.run(['which', 'brew'], capture_output=True, text=True)
        if not result.stdout.strip():
            print("Installing Homebrew...")
            install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            subprocess.run(install_cmd, shell=True, check=True)

        print("Installing PostgreSQL...")
        subprocess.run(['brew', 'install', 'postgresql@14'], check=True)
        subprocess.run(['brew', 'services', 'start', 'postgresql@14'], check=True)

        # Wait for PostgreSQL to start
        print("Waiting for PostgreSQL to start...")
        subprocess.run(['sleep', '5'])

        # Create database and user
        subprocess.run(['createdb', 'llamachat'], check=True)
        subprocess.run(['psql', 'llamachat', '-c', 
                       "CREATE USER postgres WITH PASSWORD 'postgres' SUPERUSER;"], 
                       check=True)

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
    
    print("PostgreSQL setup completed successfully!")

if __name__ == "__main__":
    setup_database() 