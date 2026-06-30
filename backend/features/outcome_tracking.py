"""
Outcome Tracking / Feedback Loop for ScholarAI

This lets students mark whether they actually applied to / got a scholarship.
That data is used to:
1. Show "X students applied" social proof on each scholarship
2. Calculate real success rates per scholarship
3. Boost match_score for scholarships with high real-world success

This is the "product thinking" feature that impresses interviewers most —
it shows you're thinking about the full product loop, not just the AI part.
"""

import sqlite3
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
DB_PATH = "scholarai.db"


def init_outcomes_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            scholarship_name TEXT,
            status TEXT,
            -- status values: 'applied', 'got_it', 'rejected', 'not_applied'
            student_category TEXT,
            student_state TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Outcomes table ready")


class OutcomeUpdate(BaseModel):
    student_name: str
    scholarship_name: str
    status: str  # "applied" | "got_it" | "rejected" | "not_applied"
    student_category: str = ""
    student_state: str = ""


@router.post("/track-outcome")
def track_outcome(outcome: OutcomeUpdate):
    """
    Call this from the frontend when a student clicks a button like
    'I applied' or 'I got this scholarship!' on a scholarship card.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO outcomes (student_name, scholarship_name, status, student_category, student_state, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        outcome.student_name, outcome.scholarship_name, outcome.status,
        outcome.student_category, outcome.student_state, datetime.utcnow()
    ))
    conn.commit()
    conn.close()
    return {"status": "saved", "message": "Thanks for the update! This helps other students."}


@router.get("/scholarship-stats/{scholarship_name}")
def get_scholarship_stats(scholarship_name: str):
    """
    Returns social proof stats for a scholarship:
    'X students applied, Y got selected'
    Use this to show on the scholarship card in the frontend.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    applied = c.execute(
        "SELECT COUNT(*) FROM outcomes WHERE scholarship_name = ? AND status IN ('applied', 'got_it', 'rejected')",
        (scholarship_name,)
    ).fetchone()[0]

    got_it = c.execute(
        "SELECT COUNT(*) FROM outcomes WHERE scholarship_name = ? AND status = 'got_it'",
        (scholarship_name,)
    ).fetchone()[0]

    conn.close()

    success_rate = round((got_it / applied) * 100) if applied > 0 else None

    return {
        "scholarship_name": scholarship_name,
        "students_applied": applied,
        "students_selected": got_it,
        "success_rate_percent": success_rate,
    }


@router.get("/admin/outcomes-dashboard")
def outcomes_dashboard():
    """
    Full analytics view — use this to show in your LinkedIn posts!
    'X total applications tracked, Y scholarships won, ₹Z total funding secured'
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    total_tracked = c.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0]
    total_won = c.execute("SELECT COUNT(*) FROM outcomes WHERE status = 'got_it'").fetchone()[0]

    top_scholarships = c.execute("""
        SELECT scholarship_name, COUNT(*) as applications
        FROM outcomes WHERE status IN ('applied', 'got_it')
        GROUP BY scholarship_name ORDER BY applications DESC LIMIT 10
    """).fetchall()

    by_category = c.execute("""
        SELECT student_category, COUNT(*) as count
        FROM outcomes WHERE student_category != ''
        GROUP BY student_category ORDER BY count DESC
    """).fetchall()

    conn.close()

    return {
        "total_outcomes_tracked": total_tracked,
        "total_scholarships_won": total_won,
        "win_rate_percent": round((total_won / total_tracked) * 100) if total_tracked > 0 else 0,
        "top_applied_scholarships": [{"name": r[0], "applications": r[1]} for r in top_scholarships],
        "by_category": [{"category": r[0], "count": r[1]} for r in by_category],
    }


def boost_score_with_outcomes(scholarship_name: str, base_score: int) -> int:
    """
    Use this inside your matching logic to boost match_score
    for scholarships with proven real-world success.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    applied = c.execute(
        "SELECT COUNT(*) FROM outcomes WHERE scholarship_name = ?", (scholarship_name,)
    ).fetchone()[0]
    got_it = c.execute(
        "SELECT COUNT(*) FROM outcomes WHERE scholarship_name = ? AND status = 'got_it'", (scholarship_name,)
    ).fetchone()[0]

    conn.close()

    if applied >= 5:  # only trust the signal with enough data
        success_rate = got_it / applied
        boost = int(success_rate * 10)  # up to +10 points
        return min(base_score + boost, 100)

    return base_score
