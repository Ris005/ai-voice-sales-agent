# 2 · Why the Audio Sounds Robotic (and how to fix it)

## Root cause
The current app calls the browser's **Web Speech API**:

```js
const u = new SpeechSynthesisUtterance(text);
window.speechSynthesis.speak(u);   // static/app.js
```

`speechSynthesis` uses whatever **operating-system voices** are installed. On most
machines those are older **concatenative / formant** voices (macOS "Samantha", Windows
"David/Zira", generic Google voices). They are:

- not **neural** (no deep-learning prosody) → flat, robotic intonation,
- inconsistent across machines (every user hears a different voice),
- unable to **clone a specific voice** (the PDF's preferred option),
- no fine control over pacing, emphasis, or emotion.

That is the audio-quality issue — it is a limitation of the *engine*, not the code.

## The fix, in one sentence
**Generate speech on the server with a neural TTS model and stream the audio
(MP3/WAV) to the browser to play** — instead of asking the browser to synthesize it.

## Quick wins (minutes) — squeeze the current engine
These do **not** make it neural, but make the default voice less grating. Already
tune-able in [`static/app.js`](../static/app.js) `speak()`:

```js
u.rate  = 1.0;    // 0.9–1.05 sounds most natural; too fast = robotic
u.pitch = 1.0;    // keep near 1.0; extremes sound synthetic
// Prefer a higher-quality installed voice if present:
voice = voices.find(v => /natural|neural|premium|google (uk|us) english/i.test(v.name)) || voice;
```

- On **macOS**, install *Enhanced/Premium* voices: System Settings → Accessibility →
  Spoken Content → System Voice → **Manage Voices** (download "Siri" / "Enhanced").
- On **Chrome**, the "Google …" voices are cloud-backed and noticeably better than
  local OS voices — prefer them (the selector already tries to).

## Real fix (recommended) — neural TTS
Pick one and follow [UPGRADE_PLAN.md](UPGRADE_PLAN.md):

| Option | Quality | Setup | Notes |
|--------|---------|-------|-------|
| **OpenAI TTS** (`tts-1` / `gpt-4o-mini-tts`) | 🟢🟢 | 1 endpoint + existing `OPENAI_API_KEY` | fastest path; 6 built-in voices |
| **Piper TTS** (PDF-suggested) | 🟢 | pip install, runs offline/CPU | free, self-hosted, fast |
| **Coqui XTTS v2** | 🟢🟢 | GPU recommended | supports **voice cloning** |
| **ElevenLabs Free Tier** (PDF-suggested) | 🟢🟢🟢 | API key | best realism + cloning; free quota |

See [TTS_OPTIONS.md](TTS_OPTIONS.md) for a full comparison and code.

## Why we shipped browser TTS first
Zero setup, no keys, works on the free Render URL, and demos instantly. It is the
**Tier A** baseline — the docs here take you to **Tier B/C** for production-quality,
human-like audio.
