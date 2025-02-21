import subprocess
import sys
import os

from app import DB_NAME, DATA_DIR

try:
    from utils import database_utils
except ImportError as e:
    print(f"Error importing database_utils: {e}")
    sys.exit(1)

def initialize_database_if_needed():
    """
    Ensure the database is set up before running the application.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(DB_NAME) or os.path.getsize(DB_NAME) == 0:
        print("Database is empty or doesn't exist. Initializing...\n")
        try:
            database_utils.run()  # Database utility is executed
        except Exception as e:
            print(f"Error initializing database: {e}")
            sys.exit(1)  # Exit if database setup fails

def run_app():
    try:
        # Initialize the database if empty or doesn't exist
        initialize_database_if_needed()

        # Start the application
        flask_process = subprocess.Popen([sys.executable, "app.py"])
        dash_process = subprocess.Popen([sys.executable, "dashboard.py"])
        upload_process = subprocess.Popen([sys.executable, "web_importer.py"])

        flask_process.wait()
        dash_process.wait()
        upload_process.wait()
    except KeyboardInterrupt:
        flask_process.terminate()
        dash_process.terminate()
        upload_process.terminate()

if __name__ == "__main__":
    run_app()
