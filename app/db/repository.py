"""Read/write helpers for the sessions table."""

import json
from datetime import datetime, timezone

from .schema import get_connection


def save_session(case_frame, narrative: str, image_path: str = None, audio_path: str = None) -> int:
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO sessions
            (input_text, emotion_scores, core_emotion, distortions, techniques,
             narrative, image_path, audio_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_frame.raw_text,
            json.dumps(case_frame.emotion_scores),
            case_frame.core_emotion,
            json.dumps(case_frame.distortions),
            json.dumps(case_frame.selected_techniques),
            narrative,
            image_path,
            audio_path,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    session_id = cur.lastrowid
    conn.close()
    return session_id


def update_image_path(session_id: int, image_path: str):
    conn = get_connection()
    conn.execute("UPDATE sessions SET image_path = ? WHERE id = ?", (image_path, session_id))
    conn.commit()
    conn.close()


def get_session(session_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_sessions(limit: int = 50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def find_recurring_themes(min_occurrences: int = 3):
    """
    Very simple recurring-theme signal (Phase 2): counts how often each
    technique id has been selected across past sessions. If a technique
    (proxy for "theme") has been selected >= min_occurrences times, surface
    a note about it so it can be folded into future narrative prompts.
    """
    conn = get_connection()
    rows = conn.execute("SELECT techniques FROM sessions").fetchall()
    conn.close()

    counts = {}
    for row in rows:
        techniques = json.loads(row["techniques"])
        for t in techniques:
            counts[t] = counts.get(t, 0) + 1

    return {t: c for t, c in counts.items() if c >= min_occurrences}
