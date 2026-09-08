"""SQLite schema and connection helper for session storage."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sessions", "reframe.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT NOT NULL,
            emotion_scores TEXT NOT NULL,      -- JSON blob
            core_emotion TEXT NOT NULL,
            distortions TEXT NOT NULL,         -- JSON list
            techniques TEXT NOT NULL,          -- JSON list of technique ids
            narrative TEXT NOT NULL,
            image_path TEXT,
            audio_path TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
