# 📞 AI Voice Sales Agent (Excel CRM)

An AI-powered voice sales agent that calls leads from an Excel sheet, holds a
natural spoken sales conversation, qualifies the prospect, books meetings, and
writes every outcome back to the **Excel file that acts as the CRM**.

Built to be **deployed in one click on Render** with a clean, modern dashboard UI.

![stack](https://img.shields.io/badge/FastAPI-Python-6c8cff) ![deploy](https://img.shields.io/badge/Deploy-Render-4ee0c1) ![voice](https://img.shields.io/badge/Voice-Browser%20TTS%2FSTT-ff6b81)

---

## ✨ What it does (maps 1:1 to the assignment)

| Requirement | How it's implemented |
|---|---|
| **Lead management** | Reads leads from `data/leads.xlsx`; only **pending** leads are callable, **completed** / **opted-out** are skipped. |
| **AI voice calling** | Live call UI. The agent **speaks** (browser speech synthesis) and **listens** to the prospect via the mic (speech recognition). Natural pacing; type-to-reply fallback for mic-free demos. |
| **Sales conversation** | Introduces the company & purpose, **qualifies** with predefined questions, answers using the **knowledge base**, and **handles objections** naturally. |
| **Meeting booking** | Detects interest, collects a **date & time**, and marks the meeting booked (or records the reason / no-answer). |
| **Excel CRM update** | After every call, writes Call Status, Lead Qualification, Conversation Summary, Customer Requirements, Objections, Follow-up Date, Meeting Date & Time, and Last Contacted timestamp. |

### Why browser voice instead of telephony?
Real phone calls need a paid telephony provider (Twilio) + a purchased number and
can't be demoed on a free Render URL. This app puts the **same agent brain** behind
a browser voice channel so it's **instantly deployable, free, and demoable**. The
conversation/CRM layer is decoupled — swapping in Twilio + LiveKit/Pipecat for real
PSTN calls only touches the transport, not the agent (see *Extending* below).

---

## 🧠 The agent brain — works with or without an API key

- **With `OPENAI_API_KEY`** → uses a live LLM (`gpt-4o-mini` by default) for replies
  and for extracting the structured CRM summary.
- **Without a key** → a built-in **rule-based sales brain** runs the full flow
  (intro → qualify → pitch → objection handling → booking → close). So the app
  **runs and demos with zero configuration and zero cost.**

The knowledge base lives in [`data/knowledge_base.md`](data/knowledge_base.md) and
the agent persona in [`prompts/system_prompt.txt`](prompts/system_prompt.txt) — edit
these to reconfigure the pitch, no code changes needed.

---

## 🚀 Deploy to Render (one click)

1. Push this folder to a Git repo (GitHub/GitLab — a free private repo is fine).
2. In Render: **New + → Blueprint**, select the repo. `render.yaml` is auto-detected.
3. (Optional) In the dashboard, add `OPENAI_API_KEY` as a secret to enable the LLM.
4. Deploy. Your agent is live at `https://<your-app>.onrender.com`.

The blueprint provisions a free web service with a health check at `/healthz`.

📖 **Full step-by-step guide, env vars, and free-tier notes:
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).**

> Also deployable anywhere that runs the `Procfile` or the `Dockerfile`
> (Railway, Fly.io, Docker, etc.), or share your localhost instantly with
> `npx ngrok http 8000`.

---

## 💻 Run locally

```bash
cd ai-voice-sales-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# optional: cp .env.example .env  and set OPENAI_API_KEY
uvicorn app.main:app --reload
```

Open **http://localhost:8000**.

> Use **Chrome or Edge** for microphone speech recognition. In any browser you can
> type the prospect's replies — the agent still speaks aloud.

---

## 🎬 Suggested 3–5 min demo flow

1. Show the **dashboard** — leads loaded from Excel, pending vs completed vs opted-out.
2. Click **Call** on a pending lead → agent greets aloud, states its purpose.
3. Answer with the mic (or type): ask about **price** → agent handles the objection.
4. Say you're **interested**, propose *"Tuesday at 3 pm"* → agent confirms the meeting.
5. Click **End call** → outcome card appears; row updates to **completed / booked / hot**.
6. Click **Download CRM (.xlsx)** → open the sheet and show the written-back columns.

---

## 🗂 Project structure

```
ai-voice-sales-agent/
├── app/
│   ├── main.py         # FastAPI app: dashboard + call/CRM API
│   ├── crm.py          # Excel read/write (openpyxl) — the CRM
│   ├── agent.py        # LLM + rule-based sales brain, call summarizer
│   ├── knowledge.py    # loads KB + system prompt
│   └── config.py       # env-driven config
├── data/
│   ├── leads.xlsx      # auto-seeded on first run
│   └── knowledge_base.md
├── prompts/system_prompt.txt
├── static/             # dashboard UI (HTML/CSS/JS, browser voice)
├── render.yaml         # Render blueprint (one-click deploy)
├── Dockerfile · Procfile · requirements.txt
```

## 🔌 API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/leads` | Leads + stats |
| `GET` | `/api/knowledge` | Knowledge base |
| `POST` | `/api/call/start` | Begin a call (`{lead_id}`) → opening line |
| `POST` | `/api/call/turn` | Prospect reply (`{session_id, text}`) → agent reply |
| `POST` | `/api/call/end` | Finalize → structured outcome, written to Excel |
| `GET` | `/download/crm` | Download the updated `.xlsx` |
| `GET` | `/healthz` | Health check |

## 🧩 Extending to real phone calls
The agent's turn/summary logic in `agent.py` is transport-agnostic. To make real
outbound PSTN calls, wire a Twilio (or LiveKit/Pipecat) media stream to
`/api/call/start` → `/api/call/turn` → `/api/call/end`, feeding STT transcripts in
and streaming TTS out. The Excel CRM layer stays exactly as-is.
