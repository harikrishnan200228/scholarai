"""
Database module for ScholarAI
Uses SQLite by default (no setup needed for development)
Switch to PostgreSQL for production by changing DATABASE_URL
"""

import os
import sqlite3
from datetime import datetime

# Default: SQLite (works out of the box, no setup needed)
# For production: set DATABASE_URL=postgresql://user:pass@host/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///scholarai.db")

DB_PATH = "scholarai.db"


def init_db():
    """Create tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            course TEXT,
            category TEXT,
            state TEXT,
            matches_count INTEGER,
            total_funding TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scholarship_name TEXT,
            student_category TEXT,
            student_state TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized")


def save_search(name, course, category, state, matches_count, total_funding):
    """Save search analytics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO searches (student_name, course, category, state, matches_count, total_funding, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, course, category, state, matches_count, total_funding, datetime.utcnow()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB save error: {e}")


def get_analytics():
    """Get basic analytics - useful for admin dashboard"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    total_searches = c.execute("SELECT COUNT(*) FROM searches").fetchone()[0]
    top_states = c.execute("""
        SELECT state, COUNT(*) as count
        FROM searches WHERE state != ''
        GROUP BY state ORDER BY count DESC LIMIT 5
    """).fetchall()
    top_categories = c.execute("""
        SELECT category, COUNT(*) as count
        FROM searches WHERE category != ''
        GROUP BY category ORDER BY count DESC
    """).fetchall()
    recent = c.execute("""
        SELECT student_name, course, matches_count, created_at
        FROM searches ORDER BY created_at DESC LIMIT 10
    """).fetchall()

    conn.close()
    return {
        "total_searches": total_searches,
        "top_states": top_states,
        "top_categories": top_categories,
        "recent_searches": recent,
    }
