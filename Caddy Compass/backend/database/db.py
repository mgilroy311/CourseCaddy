import sqlite3
import os

def get_connection():
    db_path = os.path.join(os.path.dirname(__file__), "database", "coursecaddy.db")
    return sqlite3.connect(db_path)