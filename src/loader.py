"""
This file loads the CSV file and inserts the data into the PostgreSQL database using the functions from db.py and config.py.
"""

import config
import db
import logging_config
import csv
from typing import List
from psycopg2.extensions import connection,cursor

#Keeping logger outside at module level to be accessible to all functions in this file.
logger = logging_config.setup_logging()

   

def read_file(csv_path:str | None) -> List[dict[str, str]] :
    """
    Reads the file if exists and returns the rows as a list of dictionaries. 
    If the file does not exist, raises a FileNotFoundError.'
    """

    try:
        with open(csv_path, "r") as file:
            csv_reader = csv.DictReader(file)
            rows =[row for row in csv_reader]
            logger.info(f"Successfully read {len(rows)} rows from the CSV file.")
            logger.debug(f"Rows read: {rows}")
        return rows
    except FileNotFoundError:
        logger.error(f"CSV file not found at path: {csv_path}")
        raise FileNotFoundError(f"CSV file not found at path: {csv_path}")
    

def main():
    """
    Main function to load the CSV file and insert the data into the PostgreSQL database.
    """
    
    logger.info("Starting CSV loader...")
    
    # Get database connection object
    connection_object = db.get_db_connection()
    
    # Create table if it does not exist
    db.create_table_if_not_exists(connection_object)
    
    # Read CSV file
    csv_path = config.get_csv_path()
    logger.info(f"Reading CSV from {csv_path}")
    rows = read_file(csv_path)

def record_exists(connection_object: connection, otis_id: str) -> bool:
    """
    Check if a record with the given id exists in the california_properties table.
    Returns True if the record exists, False otherwise.
    """
    try:
        record_exists_query = "SELECT 1 FROM california_properties WHERE otis_id = %s"
        postgres_cursor: cursor = connection_object.cursor()
        postgres_cursor.execute(record_exists_query, (otis_id,))
        query_result=postgres_cursor.fetchone() is not None
        postgres_cursor.close()
        return query_result
    except Exception as e:
        logger.error(f"Error checking if record exists: {e}")
        raise

def insert_record(connection_object: connection, record: dict[str, str]) -> None:
    """
    Insert a record into the california_properties table.
    If the insertion fails, log the error and raise the exception.
    """
    try:
        insert_query = """
        INSERT INTO california_properties (otis_id, address, city, state, zip_code, price, bedrooms, bathrooms, square_feet)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        postgres_cursor: cursor = connection_object.cursor()
        postgres_cursor.execute(insert_query, (
            record["otis_id"],
            record["address"],
            record["city"],
            record["state"],
            record["zip_code"],
            record["price"],
            record["bedrooms"],
            record["bathrooms"],
            record["square_feet"]
        ))
        connection_object.commit()
        postgres_cursor.close()
        logger.info(f"Inserted record with otis_id: {record['otis_id']}")
    except Exception as e:
        logger.error(f"Error inserting record with otis_id {record['otis_id']}: {e}")
        connection_object.rollback()
        raise