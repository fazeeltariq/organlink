import mysql.connector
from mysql.connector import Error

class Config:
    SECRET_KEY = 'organlink_secret_2024'
    
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'Brc5862019@123',
        'database': 'organlink'
    }

def get_db():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(**Config.DB_CONFIG)
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None