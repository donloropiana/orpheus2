import mysql.connector
import bcrypt
from contextlib import contextmanager
from dotenv import dotenv_values
import pandas as pd

# Load environment variables
config = dotenv_values(".env")
password = 'password'

# Database connection details
connection_config = {
    'host': 'jsedocc7.scrc.nyu.edu',
    'database': 'Project_Orpheus',
    'user': 'Project_Orpheus',
    'password': password
}


# Function to get a database connection
@contextmanager
def get_db_connection():
    conn = mysql.connector.connect(**connection_config)
    try:
        yield conn
    finally:
        conn.close()

# Function to get a cursor from connection
@contextmanager
def get_cursor(conn):
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()

# Function to create a new user
def create_user(username: str, password: str):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    insert_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
    with get_db_connection() as conn, get_cursor(conn) as cursor:
        cursor.execute(insert_query, (username, hashed_password))
        conn.commit()

# Function to check if a username exists
def username_exists(username: str) -> bool:
    query = "SELECT username FROM users WHERE username = %s"
    with get_db_connection() as conn, get_cursor(conn) as cursor:
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        return result is not None

# Function to verify a password
def verify_password(username: str, password: str) -> bool:
    query = "SELECT password FROM users WHERE username = %s"
    with get_db_connection() as conn, get_cursor(conn) as cursor:
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        if result:
            stored_password = result[0]
            return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
        return False

# Function to convert a table to a pandas DataFrame
# example: table_to_df('stock_data')
def table_to_df(table_name: str) -> pd.DataFrame:
    query = f"SELECT * FROM {table_name}"
    with get_db_connection() as conn, get_cursor(conn) as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    
