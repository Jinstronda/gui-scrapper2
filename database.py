import sqlite3
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)


def init_db():
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            industry TEXT,
            job_function TEXT,
            operates_in TEXT,
            scraped_at TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized: {config.DB_PATH}")


def attendee_exists(name):
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM attendees WHERE name = ?", (name,))
    result = cursor.fetchone() is not None
    conn.close()
    return result


def save_attendee(name, industry, job_function, operates_in):
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO attendees (name, industry, job_function, operates_in, scraped_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, industry, job_function, operates_in, datetime.now()))
        
        conn.commit()
        logger.info(f"Saved: {name}")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"Duplicate attendee: {name}")
        return False
    finally:
        conn.close()


def get_all_attendees():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM attendees ORDER BY scraped_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_attendee_count():
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM attendees")
    count = cursor.fetchone()[0]
    conn.close()
    return count
