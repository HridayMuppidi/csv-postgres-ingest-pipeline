"""
This file loads the CSV file and inserts the data into the PostgreSQL database using the functions from db.py and config.py.
"""

import config
import db
import logging_config
import csv
from typing import List
from psycopg2.extensions import connection,cursor
from datetime import datetime
import sys

#Keeping logger outside at module level to be accessible to all functions in this file.
logger = logging_config.setup_logging()

csv_to_database_mapping = {
    "Primary Number": "primary_number",
    "OTIS ID": "otis_id",
    "Property Number": "property_number",
    "Name": "name",
    "Aliases and Alias Types": "aliases_and_alias_types",
    "St Number": "street_number",
    "St Name": "street_name",
    "City": "city",
    "County": "county",
    "Zip": "zip_code",
    "Vicinity": "vicinity",
    "Other Geography": "other_geographical_indicators",
    "Evaluation Info":"evaluation_information",
    "District Elements":"district_elements",
    "Parent District":"parent_district",
    "Associated Resources":"associated_resources",
    "Parcel Num":"parcel_number",
    "MilePost":"mile_post",
    "Ownership":"ownership",
    "Construction Year(s)":"construction_years",
    "oCode":"ocode",
    "Date Modified":"date_modified",
    "Export Date":"export_date",
}


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
    try:
        logger.info("Starting CSV loader...")
    
        # Get database connection object
        connection_object = db.get_db_connection()
        
        # Create table if it does not exist
        db.create_table_if_not_exists(connection_object)
        
        # Read CSV file
        csv_path = config.get_csv_path()
        logger.info(f"Reading CSV from {csv_path}")
        rows = read_file(csv_path)
        
        inserted_records_count= 0
        updated_records_count=0
        for row in rows:
            is_record_existing=upsert_row(connection_object,row)
            if is_record_existing:
                updated_records_count+=1
            else:
                inserted_records_count+=1 
        logger.info(f"Number of inserted records: {inserted_records_count}")
        logger.info(f"Number of updated records: {updated_records_count}")
        
        connection_object.close()
        logger.info("Database connection closed!")
        logger.info("CSV to database loader executed successfully")

    except Exception as e:
        logger.error(f"Fatal Error: {e}")
        sys.exit(1)
    

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
        db_columns=list(csv_to_database_mapping.values())
        db_columns+=["lastupdatedt","updateuser"] #user-defined columns to be added to the table for tracking updates.
        
        columns_query=",".join(db_columns)
        values_query=",".join(["%s"]*len(db_columns))


        insert_query = f"""
        INSERT INTO california_properties ({columns_query})
        VALUES ({values_query})
        """
        postgres_cursor: cursor = connection_object.cursor()
        record_values=[record[csv_column_name]  for csv_column_name in csv_to_database_mapping.keys()]
        record_values+=[datetime.now(),config.get_update_user()]
        postgres_cursor.execute(insert_query, tuple(record_values))
        connection_object.commit()
        postgres_cursor.close()
        logger.info(f"Inserted record with otis_id: {record['OTIS ID']}")
    except Exception as e:
        logger.error(f"Error inserting record with otis_id {record['OTIS ID']}: {e}")
        connection_object.rollback()
        raise

def update_record(connection_object:connection,record:dict[str,str|None])-> None:
    """
    Update the record in california_properties table based on the record's otis id
    If the updating fails, log the error and raise the exception.
    """
    try:
        db_columns=[db_column_name for db_column_name in csv_to_database_mapping.values() if db_column_name!="otis_id" ]
        db_columns+=["lastupdatedt","updateuser"]

        set_query=",".join([f"{csv_column} = %s" for csv_column in db_columns])
        update_query=f"""
            update california_properties
            set {set_query}
            where otis_id=%s
        """
        record_values=[record[csv_record_key] for csv_record_key in csv_to_database_mapping.keys() if csv_record_key!="OTIS ID"]
        record_values+=[datetime.now(),config.get_update_user(),record["OTIS ID"]]
        postgres_cursor:cursor=connection_object.cursor()
        postgres_cursor.execute(update_query,tuple(record_values))
        connection_object.commit()
        postgres_cursor.close()
        logger.info(f"Updated the record with OTIS ID: {record['OTIS ID']}")
    except Exception as e:
        logger.error(f"Error updating record with OTIS ID: {record['OTIS ID']} with error: {e}")
        connection_object.rollback()
        raise

def upsert_row(connection_object:connection, record:dict[str,str|None])->bool:
    """
    insert or update a record in the california_properties table.
    Check if record exists first if it doesnt' exist, call the insert function, else call update function
    return if record is existing
    """
    is_record_existing=record_exists(connection_object,record["OTIS ID"])
    if is_record_existing:
        update_record(connection_object,record)     
    else:
        insert_record(connection_object,record)
    return is_record_existing


if __name__ == "__main__":
    main()