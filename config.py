import os
import mysql.connector
from mysql.connector import Error

class Config:
    SECRET_KEY = 'organlink_secret_2024'

def get_db():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('MYSQLHOST'),
            user=os.environ.get('MYSQLUSER'),
            password=os.environ.get('MYSQLPASSWORD'),
            database=os.environ.get('MYSQLDATABASE'),
            port=int(os.environ.get('MYSQLPORT', 3306))
        )
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None