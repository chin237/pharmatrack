"""
Database helper for PharmaTrack.

Run this file directly once to create pharmacy.db and set up the tables:
    python database/db.py

After that, import get_db_connection() from your Flask routes to query it.

Packaging note: when this runs as a normal Python script, paths are relative
to this file. When PyInstaller bundles it into a .exe, bundled files (like
schema.sql) get extracted to a temporary folder that disappears when the app
closes - so pharmacy.db must NOT live there, or your data would vanish every
time you close the app. Instead, the actual database file is kept next to
the .exe itself, which persists normally.
"""

import sqlite3
import os
import sys


def _get_base_dir():
    """Folder the .exe lives in (or the project folder, when not packaged) -
    this is where pharmacy.db is kept, so it persists between runs."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_resource_dir():
    """Folder where PyInstaller extracts bundled read-only files (like
    schema.sql) at runtime. Falls back to the normal project folder when
    not packaged."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


# Tests and deployment can provide a separate database path. Normal desktop
# use still defaults to pharmacy.db next to the application.
DB_PATH = os.environ.get('PHARMATRACK_DB_PATH') or os.path.join(_get_base_dir(), 'pharmacy.db')
SCHEMA_PATH = os.path.join(_get_resource_dir(), 'database', 'schema.sql') \
    if getattr(sys, 'frozen', False) \
    else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')


def get_db_connection():
    """Opens a connection to pharmacy.db. Caller is responsible for closing it."""
    conn = sqlite3.connect(DB_PATH)
    # SQLite disables foreign-key enforcement by default; it must be enabled
    # separately for every connection.
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # lets you access columns by name, e.g. row['name']
    return conn


def init_db():
    """Creates all tables if they don't already exist. Safe to run multiple times."""
    schema_path = SCHEMA_PATH
    if os.path.isdir(schema_path):
        # Defensive fallback: if a packaging mistake made this a folder
        # containing schema.sql instead of the file itself, look inside it.
        candidate = os.path.join(schema_path, 'schema.sql')
        if os.path.isfile(candidate):
            schema_path = candidate
        else:
            raise FileNotFoundError(
                f"Expected schema.sql but found a folder at {schema_path} "
                f"with no schema.sql inside it. Check the --add-data path used when packaging."
            )

    conn = get_db_connection()
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    _run_migrations(conn)
    conn.close()
    print(f"Database ready at {DB_PATH}")


def _run_migrations(conn):
    """
    Adds columns that later versions of the schema need, to databases
    created by an earlier version. CREATE TABLE IF NOT EXISTS (in schema.sql)
    only helps for brand-new databases - it does nothing for a table that
    already exists without a newer column. Safe to run every startup:
    each check only adds a column if it's actually missing.
    """
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(user)")
    existing_columns = {row[1] for row in cur.fetchall()}
    if "password_hash" not in existing_columns:
        cur.execute("ALTER TABLE user ADD COLUMN password_hash TEXT")
        conn.commit()


if __name__ == '__main__':
    init_db()
