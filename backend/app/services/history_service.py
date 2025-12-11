import json
from datetime import datetime

from ..db.database import get_connection

def save_session(transcript, fused, audio, text, video):
    conn = get_connection()
    cur = conn.cursor()

    timestamp = datetime.utcnow().isoformat()

    cur.execute("""
        INSERT INTO sessions (
            timestamp, transcript,
            fluency, grammar, coherence, readability,
            posture, gaze, movement, overall,
            audio_json, text_json, video_json, fused_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        transcript,
        fused.get("fluency"),
        fused.get("grammar"),
        fused.get("coherence"),
        fused.get("readability"),
        fused.get("video", {}).get("posture") if video else None,
        fused.get("video", {}).get("gaze") if video else None,
        fused.get("video", {}).get("movement") if video else None,
        fused.get("overall"),
        json.dumps(audio),
        json.dumps(text),
        json.dumps(video) if video else None,
        json.dumps(fused)
    ))

    conn.commit()
    conn.close()


def get_all_sessions():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM sessions ORDER BY id DESC").fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_summary():
    conn = get_connection()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT 
            AVG(fluency) AS avg_fluency,
            AVG(grammar) AS avg_grammar,
            AVG(posture) AS avg_posture,
            AVG(overall) AS avg_overall,
            COUNT(*) AS total_sessions
        FROM sessions
    """).fetchone()

    conn.close()
    return dict(rows)
