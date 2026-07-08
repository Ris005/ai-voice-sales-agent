# 🚀 Deployment Guide — Render

Deploy the AI Voice Sales Agent to a permanent public URL on
[Render](https://render.com). The repo is already prepared: it has `render.yaml`
(a Render Blueprint), a `Procfile`, a `Dockerfile`, and a clean git history.

> **Result:** a live URL like `https://ai-voice-sales-agent.onrender.com` you can put
> in your submission and demo video.

---

## Prerequisites
- A free [Render](https://render.com) account.
- A Git repo Render can read (GitHub / GitLab / Bitbucket). A **free private repo**
  is fine — Render just needs read access.

The code is committed locally already (`git log` shows the initial commit). You only
need to push it to a remote once.

---

## Step 1 — Push the code to a Git remote
Create an **empty** repo on GitHub (no README/license), then from the project folder:

```bash
cd ~/ai-voice-sales-agent
git branch -M main
git remote add origin https://github.com/<your-username>/ai-voice-sales-agent.git
git push -u origin main
```

*(GitLab/Bitbucket work the same way — just use their remote URL.)*

## Step 2 — Deploy the Blueprint on Render
1. Render dashboard → **New +** → **Blueprint**.
2. Connect your Git account and pick the `ai-voice-sales-agent` repo.
3. Render reads [`render.yaml`](../render.yaml) and shows the service. Click **Apply**.
4. Wait for the build (`pip install -r requirements.txt`) and first deploy.
5. Open the URL. Done — the agent is live.

The blueprint sets the start command, a health check at `/healthz`, and the
`COMPANY_NAME` / `AGENT_NAME` env vars automatically.

## Step 3 (optional) — Enable the live LLM voice brain
The app runs on the built-in **rule-based** brain with zero config. To use a real LLM:

- Render → your service → **Environment** → add `OPENAI_API_KEY` = your key (secret).
- Save. Render redeploys. `/healthz` will then report `"backend":"openai"`.

For **human-like audio** on top of that, follow
[UPGRADE_PLAN.md](UPGRADE_PLAN.md) (neural TTS).

---

## Manual deploy (without a Blueprint)
If you'd rather configure by hand: Render → **New +** → **Web Service** → pick the repo →

| Field | Value |
|-------|-------|
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/healthz` |
| Instance type | Free |

Add env vars as needed (`OPENAI_API_KEY`, `COMPANY_NAME`, `AGENT_NAME`).

---

## Environment variables

| Var | Default | Purpose |
|-----|---------|---------|
| `OPENAI_API_KEY` | *(unset)* | Enables live LLM; unset → rule-based brain |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model |
| `COMPANY_NAME` | `Nimbus CRM` | Branding + agent script |
| `AGENT_NAME` | `Aria` | Agent's name |
| `CRM_PATH` | `data/leads.xlsx` | CRM file location |

---

## Free-tier notes (important)
- **Cold starts:** free web services sleep after ~15 min idle; the first request then
  takes ~30–50s to wake. Fine for a demo; mention it in the video if it stalls.
- **Ephemeral disk:** free plans have no persistent disk, so the Excel CRM **resets to
  the seeded leads** whenever the instance restarts. Call edits within a session work
  fully; they just don't survive a restart. To persist, use a paid instance and
  uncomment the `disk` block in [`render.yaml`](../render.yaml).
- **Microphone:** browsers only allow mic access over **HTTPS** — Render URLs are
  HTTPS, so speech recognition works there (use Chrome/Edge). Typing always works.

---

## Post-deploy checklist
- [ ] `https://<app>.onrender.com/healthz` returns `{"status":"ok"}`
- [ ] Dashboard loads, 6 pending leads visible
- [ ] A call runs end-to-end and the row flips to completed/booked
- [ ] **Download CRM (.xlsx)** returns the updated sheet
- [ ] (if using LLM) `/healthz` shows `"backend":"openai"`

---

## Other hosts (same repo, no changes)
- **Railway / Fly.io:** use the `Dockerfile` (they auto-detect it) or the `Procfile`.
- **Any VPS / Docker:** `docker build -t voice-agent . && docker run -p 8000:8000 voice-agent`.
- **Quick temporary public link (no hosting):** run locally, then
  `npx ngrok http 8000` — shares your localhost over HTTPS for a live demo.
