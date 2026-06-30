"""
Email Deadline Reminder System for ScholarAI

Setup required:
1. Sign up free at https://signup.sendgrid.com (100 emails/day free forever)
2. Create an API key: Settings → API Keys → Create API Key → Full Access
3. Verify a sender email: Settings → Sender Authentication → Single Sender Verification
4. Add to .env:
   SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxx
   SENDER_EMAIL=your-verified-email@gmail.com

Install: pip install sendgrid apscheduler

This runs a daily background job that:
1. Checks all saved searches in the database
2. Finds scholarships with deadlines in the next 30 days
3. Sends a reminder email to each student
"""

import os
import sqlite3
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@scholarai.in")

DB_PATH = "scholarai.db"


def init_reminder_table():
    """Add email + reminder tracking to database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            student_name TEXT,
            scholarship_name TEXT,
            scholarship_deadline TEXT,
            apply_link TEXT,
            reminder_sent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_subscription(email: str, student_name: str, scholarship: dict):
    """Call this when a student wants deadline reminders for a scholarship"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO subscriptions (email, student_name, scholarship_name, scholarship_deadline, apply_link)
        VALUES (?, ?, ?, ?, ?)
    """, (
        email, student_name,
        scholarship.get("name"),
        scholarship.get("deadline"),
        scholarship.get("apply_link"),
    ))
    conn.commit()
    conn.close()


def send_reminder_email(to_email: str, student_name: str, scholarship_name: str,
                          deadline: str, apply_link: str, days_left: int):
    """Send a single reminder email via SendGrid"""
    if not SENDGRID_API_KEY:
        print("⚠️ SENDGRID_API_KEY not set, skipping email")
        return False

    subject = f"⏰ {days_left} days left: {scholarship_name} deadline"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #6366F1; padding: 24px; border-radius: 12px 12px 0 0;">
            <h2 style="color: white; margin: 0;">🎓 ScholarAI Reminder</h2>
        </div>
        <div style="padding: 24px; background: #f9fafb; border-radius: 0 0 12px 12px;">
            <p>Hi {student_name},</p>
            <p>Just a heads up — your scholarship deadline is approaching:</p>
            <div style="background: white; padding: 16px; border-radius: 8px; border-left: 4px solid #6366F1; margin: 16px 0;">
                <strong>{scholarship_name}</strong><br>
                Deadline: <strong style="color: #EF4444;">{deadline}</strong> ({days_left} days left)
            </div>
            <a href="{apply_link}" style="display: inline-block; background: #6366F1; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">
                Apply Now →
            </a>
            <p style="margin-top: 24px; color: #6b7280; font-size: 13px;">
                Don't miss out on this funding opportunity. Apply before the deadline closes.
            </p>
        </div>
    </div>
    """

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"✅ Email sent to {to_email}: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False


def check_and_send_reminders():
    """
    Run this daily. Checks all subscriptions, sends reminders for
    scholarships with deadlines in the next 30 days that haven't been reminded yet.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute("""
        SELECT id, email, student_name, scholarship_name, scholarship_deadline, apply_link
        FROM subscriptions WHERE reminder_sent = 0
    """).fetchall()

    sent_count = 0
    for row in rows:
        sub_id, email, name, sch_name, deadline_str, link = row

        days_left = estimate_days_left(deadline_str)
        if days_left is not None and 0 <= days_left <= 30:
            success = send_reminder_email(email, name, sch_name, deadline_str, link, days_left)
            if success:
                c.execute("UPDATE subscriptions SET reminder_sent = 1 WHERE id = ?", (sub_id,))
                sent_count += 1

    conn.commit()
    conn.close()
    print(f"📧 Reminder job complete: {sent_count} emails sent")


def estimate_days_left(deadline_str: str):
    """Convert 'October 2025' style strings into days remaining (rough estimate)"""
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
    }
    try:
        parts = deadline_str.lower().split()
        month_name = parts[0]
        month_num = months.get(month_name)
        if not month_num:
            return None

        year = datetime.now().year
        if len(parts) > 1 and parts[1].isdigit():
            year = int(parts[1])

        deadline_date = datetime(year, month_num, 15)  # assume mid-month
        days_left = (deadline_date - datetime.now()).days
        return days_left
    except Exception:
        return None


def start_scheduler():
    """Call this once when your FastAPI app starts up"""
    init_reminder_table()
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_send_reminders, "interval", hours=24)
    scheduler.start()
    print("✅ Email reminder scheduler started (runs every 24 hours)")

