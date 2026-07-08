# 7 · Upgrade Plan — Swap Browser TTS → Neural Server TTS

Concrete, copy-paste steps to replace the robotic browser voice with **neural
server-side audio** in *this* codebase. Uses OpenAI TTS (fastest quality jump); the
same shape works for Piper or ElevenLabs — just change `synthesize()`.

Result: the browser plays a natural MP3 returned by the server, instead of calling the
OS `speechSynthesis`.

---

## Step 1 — Add a TTS module
Create `app/tts.py`:

```python
"""Server-side neural TTS. Returns MP3 bytes the browser plays."""
from . import config

def synthesize(text: str) -> bytes | None:
    """OpenAI TTS. Returns None if no key → frontend falls back to browser voice."""
    if not config.OPENAI_API_KEY:
        return None
    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    resp = client.audio.speech.create(
        model="gpt-4o-mini-tts",           # natural, low-latency
        voice=config.TTS_VOICE,            # alloy, echo, fable, onyx, nova, shimmer
        input=text,
    )
    return resp.read()
```

## Step 2 — Config knobs
In `app/config.py` add:

```python
TTS_ENABLED = os.getenv("TTS_ENABLED", "auto")   # auto | on | off
TTS_VOICE = os.getenv("TTS_VOICE", "nova")
```

## Step 3 — Endpoint
In `app/main.py`:

```python
from fastapi import Response
from . import tts

@app.post("/api/tts")
def api_tts(body: dict):
    audio = tts.synthesize(body.get("text", ""))
    if audio is None:
        return Response(status_code=204)   # no server voice → use browser TTS
    return Response(content=audio, media_type="audio/mpeg")
```

## Step 4 — Frontend: play server audio, fall back to browser
In `static/app.js`, replace the body of `speak()`:

```js
async function speak(text, onDone) {
  setState("speaking", "Agent speaking…");
  try {
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (res.status === 200) {                        // neural audio from server
      const url = URL.createObjectURL(await res.blob());
      const audio = new Audio(url);
      audio.onended = () => { URL.revokeObjectURL(url); setState("idle", "Your turn"); onDone && onDone(); };
      await audio.play();
      return;
    }
  } catch (e) { /* fall through to browser TTS */ }
  browserSpeak(text, onDone);                        // existing speechSynthesis path
}
```

Rename the current `speak()` implementation to `browserSpeak()` so it remains the
zero-config fallback.

## Step 5 — Env + deploy
```bash
# .env / Render dashboard
OPENAI_API_KEY=sk-...
TTS_VOICE=nova
```
`render.yaml` already carries `OPENAI_API_KEY`; add `TTS_VOICE` next to it. No other
deploy change.

---

## Swapping the engine
`synthesize()` is the only thing that changes per engine:

| Want | Replace `synthesize()` body with |
|------|----------------------------------|
| **Piper** (free, offline) | `subprocess` call to Piper → return WAV bytes (media_type `audio/wav`) — see [TTS_OPTIONS.md](TTS_OPTIONS.md) §3.1 |
| **ElevenLabs** (cloned voice) | `elevenlabs` convert → MP3 bytes — see [TTS_OPTIONS.md](TTS_OPTIONS.md) §3.3 |
| **Coqui XTTS** (self-host clone) | `TTS.tts_to_file()` → read WAV — see [VOICE_CLONING.md](VOICE_CLONING.md) Route B |

## Effort / payoff
| Change | Effort | Audio quality |
|--------|:------:|:-------------:|
| Tune `rate`/`pitch` + pick better OS voice | 5 min | 🟠→🟠+ |
| OpenAI TTS (this plan) | ~30 min | 🟠→🟢🟢 |
| ElevenLabs cloned voice | ~1 hr | 🟢🟢→🟢🟢🟢 |
| Full streaming pipeline (barge-in) | 1–2 days | 🟢🟢🟢 + interruption |

Start with the OpenAI TTS swap — biggest quality gain for the least work.
