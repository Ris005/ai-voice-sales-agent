# 5 · Voice Cloning (the PDF's "preferred")

> "Use a human-like AI voice (**voice cloning preferred**)."

Voice cloning makes the agent speak in a **specific target voice** (e.g. your best
salesperson, or a branded persona) instead of a generic TTS voice. Two practical routes.

## Route A — ElevenLabs (easiest, free tier)
Best realism, streaming, hosted. Free tier includes **Instant Voice Cloning**.

1. Record/upload ~1–3 minutes of clean reference audio in the ElevenLabs dashboard.
2. It returns a `voice_id`.
3. Use that `voice_id` in the TTS call:

```python
from elevenlabs.client import ElevenLabs
el = ElevenLabs(api_key="...")

def say(text: str, voice_id: str) -> bytes:
    return b"".join(el.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",   # or eleven_turbo_v2_5 for low latency
        text=text,
        output_format="mp3_44100_128",
    ))
```

Set the voice via env so it's configurable, mirroring the app's existing pattern:
```bash
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
```

## Route B — Coqui XTTS v2 (self-hosted, no per-call cost)
Zero-shot cloning from ~6 seconds of reference audio. GPU strongly recommended.

```python
# pip install TTS
from TTS.api import TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")

def clone_say(text: str, ref_wav: str, out: str = "out.wav"):
    tts.tts_to_file(text=text, speaker_wav=ref_wav, language="en", file_path=out)
```

## Route C — Piper fine-tuning (advanced)
Piper can be fine-tuned on a dataset to approximate a voice, but it needs a labeled
corpus and training time — heavier than A or B. Use only if you must stay fully offline
and free and can invest in training.

## Legal / ethical note
Only clone a voice you **own or have explicit written consent** to use. ElevenLabs and
Coqui both require you to confirm rights to the reference audio. For sales calls, also
disclose AI use where local regulations require it.

## Recommendation
- **Fastest, best quality:** ElevenLabs free tier (Route A).
- **No per-call cost / on-prem:** Coqui XTTS (Route B).

Wire whichever you pick into the server TTS endpoint from
[UPGRADE_PLAN.md](UPGRADE_PLAN.md) — the browser just plays the returned audio.
