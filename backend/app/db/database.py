# backend/app/db/database.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "fluentiq.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        transcript TEXT,

        fluency INTEGER,
        grammar INTEGER,
        coherence INTEGER,
        readability REAL,
        posture INTEGER,
        gaze INTEGER,
        movement INTEGER,
        overall INTEGER,

        audio_json TEXT,
        text_json TEXT,
        video_json TEXT,
        fused_json TEXT
    )
    """)

    conn.commit()
    conn.close()
