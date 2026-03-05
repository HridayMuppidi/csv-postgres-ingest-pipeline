'''
This file setups the basic configurations for databse connection and other configurations for the application.
'''
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_db_config() ->dict[str,str | None]:
    """Load and return database configuration from environment variables."""
    return {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD")
    }


def get_csv_path()-> str | None :
    """Return the CSV file path from environment variables."""
    return os.getenv("CSV_PATH")


def get_update_user()-> str | None:
    """Return the update user from environment variables."""
    return os.getenv("UPDATE_USER")