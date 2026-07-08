"""The sales brain. Two interchangeable backends behind one interface:

  * LLM backend  — uses OpenAI when OPENAI_API_KEY is set (natural, flexible).
  * Rule backend — a deterministic script + keyword logic used as a zero-config
                   fallback so the whole app runs, and demos, without any keys.

Both produce (a) the next spoken reply during a call and (b) a structured CRM
outcome (qualification, summary, requirements, objections, meeting time) at the end.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta

from . import config, knowledge

# ---------------------------------------------------------------------------
# OpenAI client (lazy — only created if a key is present)
# ---------------------------------------------------------------------------
_client = None


def _openai():
    global _client
    if not config.OPENAI_API_KEY:
        return None
    if _client is None:
        from openai import OpenAI

        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


def backend_name() -> str:
    return "openai" if config.OPENAI_API_KEY else "rule-based"


# ---------------------------------------------------------------------------
# Opening line — how the agent starts every call
# ---------------------------------------------------------------------------
def opening_line(lead: dict) -> str:
    name = (str(lead.get("Name") or "there").split() or ["there"])[0]
    return (
        f"Hi {name}, this is {config.AGENT_NAME} calling from {config.COMPANY_NAME}. "
        f"Do you have a quick minute? I'd love to show you how we help sales teams "
        f"stop losing follow-ups."
    )


# ---------------------------------------------------------------------------
# Next reply during the call
# ---------------------------------------------------------------------------
def next_reply(lead: dict, history: list[dict]) -> str:
    client = _openai()
    if client is not None:
        try:
            return _llm_reply(client, lead, history)
        except Exception:
            pass  # fall through to the rule backend on any API failure
    return _rule_reply(lead, history)


def _llm_reply(client, lead: dict, history: list[dict]) -> str:
    messages = [{"role": "system", "content": knowledge.build_system_prompt(lead)}]
    for turn in history:
        role = "assistant" if turn["speaker"] == "agent" else "user"
        messages.append({"role": role, "content": turn["text"]})
    resp = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        temperature=0.6,
        max_tokens=120,
    )
    return resp.choices[0].message.content.strip()


# --- Rule-based conversation script ---------------------------------------
# A compact state machine that moves intro -> qualify -> needs -> pitch ->
# objection handling -> booking -> close, reacting to keywords in the reply.
_QUALIFY_STEPS = [
    "To point you the right way — how big is your sales team right now?",
    "Got it. What are you using today to track leads and follow-ups?",
    "And what's the single biggest headache with that setup?",
]


def _last_prospect(history: list[dict]) -> str:
    for turn in reversed(history):
        if turn["speaker"] == "prospect":
            return turn["text"].lower()
    return ""


def _rule_reply(lead: dict, history: list[dict]) -> str:
    text = _last_prospect(history)
    agent_turns = sum(1 for t in history if t["speaker"] == "agent")

    # Hard stops first.
    if any(k in text for k in ["do not call", "don't call", "remove me", "not interested at all", "stop calling"]):
        return "Understood, I'll take you off our list. Sorry to bother you — have a great day!"
    if any(k in text for k in ["busy", "bad time", "call later", "call back"]):
        return "No problem at all — when's a better time for a quick five-minute call?"

    # Objection handling — pull straight from the knowledge base facts.
    if any(k in text for k in ["expensive", "cost", "price", "pricing", "how much", "afford"]):
        return ("Totally fair. Plans start at ₹499 per user with a 14-day free trial and no "
                "lock-in — most teams save more in recovered follow-ups. Want me to set up the trial?")
    if any(k in text for k in ["already have", "already use", "using another", "have a crm"]):
        return ("Makes sense — the nice part is our two-way Excel and Sheets sync, so there's no "
                "risky migration. You can run both side by side. Could I show you in a short demo?")
    if any(k in text for k in ["no time", "too busy to set", "setup", "hard to set"]):
        return ("That's the best part — we import straight from your spreadsheet and most teams are "
                "live in under a day, with our help, free. Shall we book a 20-minute walkthrough?")
    if any(k in text for k in ["team", "ask my", "manager", "boss", "colleague"]):
        return "Happy to include them — should we book a short demo with your team on the call?"

    # Booking intent.
    if any(k in text for k in ["yes", "sure", "sounds good", "interested", "okay", "ok", "let's", "book", "demo", "meeting"]):
        if _find_datetime(text):
            when = _find_datetime(text)
            return f"Perfect — I've got you down for {when}. You'll get a calendar invite by email. Anything else before I let you go?"
        return "Great! What day and time work best for a 20-minute demo this week?"

    # Otherwise walk the qualification script, then pitch and ask to book.
    if agent_turns - 1 < len(_QUALIFY_STEPS):
        return _QUALIFY_STEPS[agent_turns - 1]
    return ("Based on that, Nimbus would cut your manual data entry and make sure no follow-up "
            "slips. Can I book you a quick 20-minute demo this week to show you?")


# ---------------------------------------------------------------------------
# Datetime extraction for meeting booking
# ---------------------------------------------------------------------------
_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _find_datetime(text: str) -> str | None:
    text = text.lower()
    day = None
    if "tomorrow" in text:
        day = (datetime.now() + timedelta(days=1)).strftime("%A")
    elif "today" in text:
        day = datetime.now().strftime("%A")
    else:
        for wd in _WEEKDAYS:
            if wd in text:
                day = wd.capitalize()
                break
    time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text)
    time_str = None
    if time_match:
        hour = time_match.group(1)
        minute = time_match.group(2) or "00"
        ampm = time_match.group(3)
        time_str = f"{hour}:{minute} {ampm.upper()}"
    if day and time_str:
        return f"{day} at {time_str}"
    if day:
        return f"{day} (time TBD)"
    if time_str:
        return time_str
    return None


# ---------------------------------------------------------------------------
# End-of-call structured outcome for the CRM
# ---------------------------------------------------------------------------
def summarize_call(lead: dict, history: list[dict]) -> dict:
    client = _openai()
    if client is not None:
        try:
            return _llm_summary(client, lead, history)
        except Exception:
            pass
    return _rule_summary(lead, history)


_SUMMARY_SCHEMA_HINT = (
    'Return ONLY compact JSON with keys: '
    '"call_status" (one of booked, not-interested, no-answer, callback, opted-out), '
    '"qualification" (one of hot, warm, cold, unqualified), '
    '"summary" (<=2 sentences), "requirements" (short phrase or ""), '
    '"objections" (short phrase or ""), "meeting" (e.g. "Tuesday at 3:00 PM" or ""), '
    '"follow_up" (YYYY-MM-DD or "").'
)


def _llm_summary(client, lead: dict, history: list[dict]) -> dict:
    transcript = "\n".join(f"{t['speaker']}: {t['text']}" for t in history)
    resp = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You extract structured CRM data from a sales call transcript. " + _SUMMARY_SCHEMA_HINT},
            {"role": "user", "content": transcript or "(no conversation)"},
        ],
        temperature=0,
        response_format={"type": "json_object"},
        max_tokens=300,
    )
    data = json.loads(resp.choices[0].message.content)
    return _normalize_summary(data, lead, history)


def _rule_summary(lead: dict, history: list[dict]) -> dict:
    joined = " ".join(t["text"].lower() for t in history if t["speaker"] == "prospect")
    agent_joined = " ".join(t["text"] for t in history if t["speaker"] == "agent")
    prospect_turns = [t for t in history if t["speaker"] == "prospect"]

    meeting = ""
    for t in reversed(history):
        found = _find_datetime(t["text"])
        if found and ("PM" in found or "AM" in found):
            meeting = found
            break

    call_status = "no-answer"
    qualification = "cold"
    if any(k in joined for k in ["do not call", "don't call", "remove me", "stop calling"]):
        call_status, qualification = "opted-out", "unqualified"
    elif meeting or any(k in joined for k in ["book", "demo", "meeting", "sounds good", "interested", "yes let"]):
        call_status, qualification = "booked", "hot"
    elif any(k in joined for k in ["not interested", "no thanks", "not right now", "no thank"]):
        call_status, qualification = "not-interested", "cold"
    elif any(k in joined for k in ["call later", "call back", "busy", "another time"]):
        call_status, qualification = "callback", "warm"
    elif len(prospect_turns) >= 2:
        call_status, qualification = "callback", "warm"

    objections = []
    for key, label in [("expensive", "price"), ("cost", "price"), ("price", "price"),
                       ("already", "existing tool"), ("time", "setup effort"), ("team", "needs team buy-in")]:
        if key in joined and label not in objections:
            objections.append(label)

    requirements = ""
    for kw in ["follow", "track", "integrat", "sheet", "excel", "report", "forecast", "whatsapp", "team"]:
        if kw in joined:
            requirements = "Mentioned needs around " + ", ".join(
                sorted({k for k in ["follow-ups", "tracking", "integrations", "reporting"] if k[:4] in joined or k[:5] in joined})
            ) or "general lead tracking"
            break

    summary = _plain_summary(lead, history, call_status)
    follow_up = ""
    if call_status in ("callback", "not-interested"):
        follow_up = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

    return _normalize_summary(
        {
            "call_status": call_status,
            "qualification": qualification,
            "summary": summary,
            "requirements": requirements,
            "objections": ", ".join(objections),
            "meeting": meeting,
            "follow_up": follow_up,
        },
        lead,
        history,
    )


def _plain_summary(lead: dict, history: list[dict], call_status: str) -> str:
    turns = len([t for t in history if t["speaker"] == "prospect"])
    name = str(lead.get("Name") or "The lead").split()[0]
    if call_status == "booked":
        return f"{name} was interested and a demo was booked. {turns} prospect turns."
    if call_status == "opted-out":
        return f"{name} asked not to be contacted; marked opted-out."
    if call_status == "not-interested":
        return f"{name} was not interested at this time. {turns} prospect turns."
    if call_status == "callback":
        return f"{name} asked to reconnect later; follow-up scheduled. {turns} prospect turns."
    return f"No meaningful conversation captured with {name}."


def _normalize_summary(data: dict, lead: dict, history: list[dict]) -> dict:
    valid_status = {"booked", "not-interested", "no-answer", "callback", "opted-out"}
    valid_qual = {"hot", "warm", "cold", "unqualified"}
    status = str(data.get("call_status", "")).lower().strip()
    qual = str(data.get("qualification", "")).lower().strip()
    if status not in valid_status:
        status = "no-answer"
    if qual not in valid_qual:
        qual = "cold"

    # Map to the CRM's top-level Status column.
    if status == "opted-out":
        lead_status = "opted-out"
    else:
        lead_status = "completed"

    return {
        "Status": lead_status,
        "Call Status": status,
        "Lead Qualification": qual,
        "Conversation Summary": str(data.get("summary", "")).strip(),
        "Customer Requirements": str(data.get("requirements", "")).strip(),
        "Objections Raised": str(data.get("objections", "")).strip(),
        "Follow-up Date": str(data.get("follow_up", "")).strip(),
        "Meeting Date & Time": str(data.get("meeting", "")).strip(),
    }
