"""
WhatsApp Bot for ScholarAI
Students message a phone number on WhatsApp, fill profile via chat,
and get scholarship matches sent back as a WhatsApp message.

Setup required:
1. Sign up free at https://www.twilio.com/try-twilio
2. Go to Console → Messaging → Try it out → Send a WhatsApp message
3. You get a Twilio Sandbox number (free for testing)
4. Get your Account SID and Auth Token from Twilio Console dashboard
5. Add to .env:
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxxxxxx
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886   (Twilio sandbox number)

Install: pip install twilio
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
import os
import json
import re

router = APIRouter()

# In-memory session storage (use Redis in production)
# Tracks each user's conversation state by phone number
sessions = {}

QUESTIONS = [
    ("name", "👋 Welcome to ScholarAI! Let's find your scholarships.\n\nWhat's your full name?"),
    ("course", "Great! What course are you studying? (e.g. B.Tech Computer Science)"),
    ("year", "Which year are you in? (e.g. 2nd Year)"),
    ("percentage", "What are your marks/CGPA? (e.g. 85% or 8.5 CGPA)"),
    ("income", "What's your family's annual income? (e.g. 3 LPA)"),
    ("category", "What's your category? (General/OBC/SC/ST/EWS/Minority)"),
    ("state", "Which state are you from?"),
]


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
):
    """
    Twilio calls this URL every time a student sends a WhatsApp message.
    We walk them through questions one by one, then call the matching engine.
    """
    phone = From  # e.g. "whatsapp:+919876543210"
    text = Body.strip()
    resp = MessagingResponse()
    msg = resp.message()

    # Start new session
    if phone not in sessions:
        sessions[phone] = {"step": 0, "data": {}}
        msg.body(QUESTIONS[0][1])
        return PlainTextResponse(str(resp), media_type="application/xml")

    session = sessions[phone]
    step = session["step"]

    # Restart command
    if text.lower() in ["restart", "start", "hi", "hello"]:
        sessions[phone] = {"step": 0, "data": {}}
        msg.body(QUESTIONS[0][1])
        return PlainTextResponse(str(resp), media_type="application/xml")

    # Save answer for current question
    if step < len(QUESTIONS):
        key = QUESTIONS[step][0]
        session["data"][key] = text
        session["step"] += 1

        # Ask next question
        if session["step"] < len(QUESTIONS):
            next_q = QUESTIONS[session["step"]][1]
            msg.body(next_q)
        else:
            # All questions answered — run matching
            msg.body("🔍 Finding your scholarships... give me a few seconds and send 'results' to check!")
            # In production: trigger async job here, then send results via Twilio API push message
            results_text = format_results_message(session["data"])
            msg.body(results_text)
            del sessions[phone]  # reset for next time

        return PlainTextResponse(str(resp), media_type="application/xml")

    return PlainTextResponse(str(resp), media_type="application/xml")


def format_results_message(profile_data: dict) -> str:
    """
    Calls the same matching logic used by the web app,
    formats it nicely for WhatsApp (no markdown, use emojis)
    """
    # Import here to avoid circular imports
    from main import basic_filter, build_fallback_result, StudentProfile

    profile = StudentProfile(
        name=profile_data.get("name", ""),
        course=profile_data.get("course", ""),
        year=profile_data.get("year", ""),
        percentage=profile_data.get("percentage", ""),
        income=profile_data.get("income", ""),
        category=profile_data.get("category", ""),
        state=profile_data.get("state", ""),
    )

    matches = basic_filter(profile)[:5]
    result = build_fallback_result(profile, matches)

    text = f"🎓 *{result['summary']}*\n\n"
    text += f"💰 Total potential funding: {result['total_funding']}\n\n"
    text += "*Your Top Matches:*\n\n"

    for i, m in enumerate(result["matches"][:5], 1):
        text += f"{i}. *{m['name']}*\n"
        text += f"   💵 {m['amount']}\n"
        text += f"   📅 Deadline: {m['deadline']}\n"
        text += f"   🔗 {m['apply_link']}\n\n"

    text += "Type 'restart' to search again!"
    return text
