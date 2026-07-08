"""FastAPI application: serves the dashboard UI and the call/CRM JSON API.

Call flow:
  start -> (turn, turn, ...) -> end
Sessions live in memory for the duration of a call; the durable record is the
Excel CRM, which is written on `end`.
"""
from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import agent, config, crm, knowledge

app = FastAPI(title="AI Voice Sales Agent", version="1.0.0")

# Active call sessions: session_id -> {lead, history}
_SESSIONS: dict[str, dict] = {}


@app.on_event("startup")
def _startup() -> None:
    crm.ensure_crm_exists()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class StartCall(BaseModel):
    lead_id: str


class Turn(BaseModel):
    session_id: str
    text: str


class EndCall(BaseModel):
    session_id: str


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.get("/api/config")
def api_config():
    return {
        "company": config.COMPANY_NAME,
        "agent": config.AGENT_NAME,
        "backend": agent.backend_name(),
    }


@app.get("/api/leads")
def api_leads():
    return {"leads": crm.get_leads(), "stats": crm.stats()}


@app.get("/api/knowledge")
def api_knowledge():
    return {"knowledge": knowledge.load_knowledge()}


@app.post("/api/call/start")
def api_start(body: StartCall):
    lead = crm.get_lead(body.lead_id)
    if lead is None:
        raise HTTPException(404, "Lead not found")
    if str(lead.get("Status", "")).lower() == "opted-out":
        raise HTTPException(400, "Lead has opted out and cannot be called")

    session_id = uuid.uuid4().hex
    opening = agent.opening_line(lead)
    history = [{"speaker": "agent", "text": opening}]
    _SESSIONS[session_id] = {"lead": lead, "history": history}
    return {"session_id": session_id, "lead": lead, "reply": opening}


@app.post("/api/call/turn")
def api_turn(body: Turn):
    session = _SESSIONS.get(body.session_id)
    if session is None:
        raise HTTPException(404, "Call session not found or already ended")
    session["history"].append({"speaker": "prospect", "text": body.text})
    reply = agent.next_reply(session["lead"], session["history"])
    session["history"].append({"speaker": "agent", "text": reply})
    return {"reply": reply, "history": session["history"]}


@app.post("/api/call/end")
def api_end(body: EndCall):
    session = _SESSIONS.pop(body.session_id, None)
    if session is None:
        raise HTTPException(404, "Call session not found or already ended")
    outcome = agent.summarize_call(session["lead"], session["history"])
    updated = crm.update_lead(session["lead"]["Lead ID"], outcome)
    return {"outcome": outcome, "lead": updated, "history": session["history"]}


@app.get("/download/crm")
def download_crm():
    crm.ensure_crm_exists()
    return FileResponse(
        config.CRM_PATH,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="leads_crm.xlsx",
    )


@app.get("/healthz")
def healthz():
    return JSONResponse({"status": "ok", "backend": agent.backend_name()})


# Static UI last so /api/* wins routing.
app.mount("/", StaticFiles(directory=str(config.STATIC_DIR), html=True), name="static")
