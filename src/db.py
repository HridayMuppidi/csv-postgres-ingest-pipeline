'''
This file contains the functions to connect to the PostgreSQL database and 
create the california properties table if it does not exist.
'''
import psycopg2
import config
import logging_config
from psycopg2.extensions import connection,cursor

logger= logging_config.setup_logging()
    
def get_db_connection() ->connection:
    '''Create a connection to the PostgreSQL database using the configuration from config.py
        if connection fails, log the error and raise the exception.
    '''
    db_config : dict[str,str | None]= config.get_db_config()
    try:
        connection_object: connection= psycopg2.connect(
            database=db_config["dbname"],
            user=db_config["user"],
            password=db_config["password"],
            host=db_config["host"],
            port=db_config["port"]
        )
        return connection_object
    except Exception as e:
        logger.error(f"Error connecting to the database: {e}")
        raise

def create_table_if_not_exists(connection_object: connection)->None:
    '''
    Create the california properties table if it does not exist in the database using the provided connection object.
    If the table creation fails, log the error and raise the exception.
    '''
    try:
        #Read the SQL Query to create the table from the create_table.sql file and execute it using the provided connection object by creating a cursor and committing it.
        with open("sql/create_table.sql", "r") as file:
            create_table_query = file.read()
    
        postgres_cursor = connection_object.cursor()
        postgres_cursor.execute(create_table_query)
        #since the table creation is a DDL operation, we need to commit the changes to the database.
        #Not needed when just reading data using select queries.
        connection_object.commit() 
        
        postgres_cursor.close()
        logger.info("California Properties Table created successfully or already exists.")
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        connection_object.rollback()
        raise