"""
Database helper for PharmaTrack.

Run this file directly once to create pharmacy.db and set up the tables:
    python database/db.py

After that, import get_db_connection() from your Flask routes to query it.
"""

import sqlite3
import os

# pharmacy.db lives in the project root, one level up from this file
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pharmacy.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')


def get_db_connection():
    """Opens a connection to pharmacy.db. Caller is responsible for closing it."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you access columns by name, e.g. row['name']
    return conn


def init_db():
    """Creates all tables if they don't already exist. Safe to run multiple times."""
    conn = get_db_connection()
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"Database ready at {DB_PATH}")


if __name__ == '__main__':
    init_db()