from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import traceback
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from database import save_search, init_db

load_dotenv()

app = FastAPI(title="ScholarAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "scholarships.json"

print(f"Looking for data at: {DATA_FILE}")
print(f"File exists: {DATA_FILE.exists()}")

with open(DATA_FILE) as f:
    SCHOLARSHIPS = json.load(f)

print(f"✅ Loaded {len(SCHOLARSHIPS)} scholarships")

API_KEY = os.getenv("GROK_API_KEY")
print(f"Grok API Key set: {'YES - ' + API_KEY[:12] + '...' if API_KEY else 'NO - CHECK .env FILE!'}")

# Grok uses OpenAI-compatible API
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.x.ai/v1",
)

@app.on_event("startup")
def startup():
    init_db()

class StudentProfile(BaseModel):
    name: str
    course: str
    year: str = ""
    percentage: str = ""
    income: str = ""
    category: str = ""
    state: str = ""
    interests: str = ""

@app.get("/")
def root():
    return {"message": "ScholarAI API running", "scholarships": len(SCHOLARSHIPS)}

@app.get("/health")
def health():
    return {"status": "ok", "scholarships": len(SCHOLARSHIPS)}

@app.post("/find-scholarships")
async def find_scholarships(profile: StudentProfile):
    try:
        print(f"\n--- New request for: {profile.name} ---")

        basic_matches = basic_filter(profile)
        print(f"Basic filter found: {len(basic_matches)} matches")
        if not basic_matches:
            basic_matches = SCHOLARSHIPS[:8]

        try:
            print("Calling Grok AI...")
            ai_result = await ai_rank_and_explain(profile, basic_matches[:8])
            print(f"✅ Grok returned {len(ai_result.get('matches', []))} matches")
            result = ai_result
        except Exception as ai_err:
            print(f"⚠️ AI failed ({ai_err}), using rule-based fallback")
            result = build_fallback_result(profile, basic_matches[:7])

        try:
            save_search(profile.name, profile.course, profile.category,
                        profile.state, len(result.get("matches", [])),
                        result.get("total_funding", ""))
        except:
            pass

        return result

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def basic_filter(profile: StudentProfile):
    matches = []

    try:
        pct_str = profile.percentage.replace("%","").replace("CGPA","").replace("cgpa","").strip()
        percentage = float(pct_str.split()[0]) if pct_str else 65.0
        if percentage <= 10:
            percentage = percentage * 9.5
    except:
        percentage = 65.0

    try:
        inc_str = (profile.income.replace("₹","").replace("LPA","").replace("lpa","")
                   .replace("L","").replace("l","").replace(",","").strip())
        income_val = float(inc_str) if inc_str else 5.0
        income = income_val * 100000 if income_val < 100 else income_val
    except:
        income = 500000

    for s in SCHOLARSHIPS:
        score = 0
        states = s.get("states", ["All India"])

        if profile.category and profile.category in s.get("categories", []):
            score += 30
        elif not profile.category or "General" in s.get("categories", []):
            score += 10

        if "All India" in states:
            score += 20
        elif profile.state and profile.state in states:
            score += 25

        if percentage >= s.get("min_percentage", 0):
            score += 25

        if income <= s.get("income_limit", 9999999):
            score += 20

        course_keywords = s.get("course_keywords", [])
        if course_keywords and any(kw.lower() in profile.course.lower() for kw in course_keywords):
            score += 15

        if score >= 40:
            matches.append({**s, "basic_score": score})

    return sorted(matches, key=lambda x: x["basic_score"], reverse=True)


def build_fallback_result(profile: StudentProfile, matches: list):
    first_name = profile.name.split()[0] if profile.name else "Student"
    total = sum(m.get("amount", 0) for m in matches)

    formatted_matches = []
    for i, m in enumerate(matches):
        score = max(95 - (i * 5), 60)
        formatted_matches.append({
            "name": m.get("name", ""),
            "provider": m.get("provider", ""),
            "amount": f"₹{m.get('amount', 0):,} per {m.get('per', 'year')}",
            "eligibility": m.get("eligibility", ""),
            "deadline": m.get("deadline_month", "Check website"),
            "match_score": score,
            "match_reason": f"Matches your {profile.category or 'general'} category and {profile.course} profile.",
            "apply_link": m.get("apply_url", "https://scholarships.gov.in"),
            "category": m.get("type", "Government"),
        })

    return {
        "matches": formatted_matches,
        "total_funding": f"₹{total:,}",
        "summary": f"Hi {first_name}! We found {len(matches)} scholarships matching your profile. Apply before deadlines — most require Aadhaar-linked bank account.",
        "tips": [
            "Apply on scholarships.gov.in using Aadhaar-based OTR registration",
            "Keep marksheet, income certificate and caste certificate scanned and ready",
            "You can receive one central + one state scholarship simultaneously",
        ]
    }


async def ai_rank_and_explain(profile: StudentProfile, matches: list):
    system_prompt = """You are ScholarAI, an expert scholarship counselor for Indian students.
Return ONLY raw valid JSON. No markdown, no code blocks, no explanation whatsoever.

Exact format:
{
  "matches": [
    {
      "name": "Scholarship Name",
      "provider": "Organization",
      "amount": "₹20,000 per year",
      "eligibility": "Who qualifies",
      "deadline": "October 2025",
      "match_score": 90,
      "match_reason": "Personal reason why this fits this specific student",
      "apply_link": "https://...",
      "category": "Government"
    }
  ],
  "total_funding": "₹1,50,000",
  "summary": "2 sentence personal message using student first name",
  "tips": ["Tip 1", "Tip 2", "Tip 3"]
}

category must be one of: Government, Private, Merit, Need-based, Research, Sports, Minority
Return 5-7 matches sorted by match_score descending.
IMPORTANT: Return ONLY the JSON. No other text."""

    clean_matches = []
    for m in matches:
        clean_matches.append({
            "name": m.get("name", ""),
            "provider": m.get("provider", ""),
            "amount": f"₹{m.get('amount', 0):,} per {m.get('per','year')}",
            "eligibility": m.get("eligibility", ""),
            "deadline": m.get("deadline_month", "Check website"),
            "type": m.get("type", ""),
            "apply_url": m.get("apply_url", "https://scholarships.gov.in"),
        })

    user_msg = f"""Student Profile:
Name: {profile.name}
Course: {profile.course}
Year: {profile.year}
Marks: {profile.percentage}
Family Income: {profile.income}
Category: {profile.category}
State: {profile.state}
Achievements: {profile.interests or 'None'}

Scholarships to rank:
{json.dumps(clean_matches, indent=2)}

Return ONLY the JSON object."""

    response = client.chat.completions.create(
        model="grok-3-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ],
        max_tokens=2000,
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    print(f"Grok response preview: {raw[:150]}")

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)