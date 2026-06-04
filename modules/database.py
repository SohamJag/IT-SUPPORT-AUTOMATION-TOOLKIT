import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "toolkit.db")

def get_db_connection():
    """Establish a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            report_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            format TEXT NOT NULL,
            summary TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def add_report(report_name, file_path, format_type, summary=None):
    """Add a new generated report record to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reports (report_name, file_path, format, summary) VALUES (?, ?, ?, ?)",
        (report_name, file_path, format_type, summary)
    )
    conn.commit()
    report_id = cursor.lastrowid
    conn.close()
    return report_id

def get_reports():
    """Retrieve all report records sorted by latest timestamp first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_report(report_id):
    """Delete a report record from the database by ID and return its file path if found."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get file path first
    cursor.execute("SELECT file_path FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    file_path = row["file_path"] if row else None
    
    if file_path:
        cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        conn.commit()
    
    conn.close()
    return file_path
