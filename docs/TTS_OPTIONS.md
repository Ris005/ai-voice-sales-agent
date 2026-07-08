# 3 · Text-to-Speech (TTS) Options

The engine that turns the agent's text into spoken audio. Ordered from the current
baseline up to studio-quality / cloned voices.

## Comparison

| Engine | Realism | Cost | Runs | Cloning | Latency | PDF-listed |
|--------|:------:|:----:|:----:|:------:|:------:|:----------:|
| Browser `speechSynthesis` (current) | 🟠 | free | client | ❌ | instant | — |
| **Piper TTS** | 🟢 | free | CPU/offline | ❌ (fine-tune only) | ~low | ✅ |
| **OpenAI TTS** (`tts-1`, `gpt-4o-mini-tts`) | 🟢🟢 | cheap | API | ❌ (preset voices) | low | ✅ (OpenAI API) |
| **Coqui XTTS v2** | 🟢🟢 | free | GPU best | ✅ zero-shot | med | — |
| **ElevenLabs** (Free Tier) | 🟢🟢🟢 | free quota → paid | API | ✅ | low (streaming) | ✅ |

## 3.1 Piper TTS (free, offline — PDF-suggested)
Fast neural TTS that runs on CPU. Great for a free, self-hosted upgrade.

```bash
pip install piper-tts
# download a voice model (.onnx), e.g. en_US-amy-medium
python -m piper --model en_US-amy-medium.onnx --output_file out.wav <<< "Hello from Nimbus CRM."
```

Server sketch (FastAPI) to add to this app:
```python
# app/tts.py
import subprocess, tempfile

def piper_wav(text: str) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run(["python", "-m", "piper",
                        "--model", "en_US-amy-medium.onnx",
                        "--output_file", f.name],
                       input=text.encode(), check=True)
        return open(f.name, "rb").read()
```

## 3.2 OpenAI TTS (fastest quality jump — recommended)
If `OPENAI_API_KEY` is already set for the LLM, reuse it for voice. One call:

```python
# app/tts.py
from openai import OpenAI
client = OpenAI()

def openai_mp3(text: str, voice: str = "alloy") -> bytes:
    # voices: alloy, echo, fable, onyx, nova, shimmer
    resp = client.audio.speech.create(model="gpt-4o-mini-tts", voice=voice, input=text)
    return resp.read()
```

Expose it and play in the browser (see [UPGRADE_PLAN.md](UPGRADE_PLAN.md)).

## 3.3 ElevenLabs (best realism + cloning — PDF-suggested)
Highest quality and supports **voice cloning** on the free tier.

```python
# pip install elevenlabs
from elevenlabs.client import ElevenLabs
el = ElevenLabs(api_key="...")

def eleven_mp3(text: str, voice_id: str) -> bytes:
    audio = el.text_to_speech.convert(
        voice_id=voice_id, model_id="eleven_turbo_v2_5",
        text=text, output_format="mp3_44100_128",
    )
    return b"".join(audio)
```

Streaming variant (`.convert_as_stream`) gives sub-second first-audio for natural flow.

## 3.4 Coqui XTTS v2 (self-hosted cloning)
Open-source, clones a voice from ~6 seconds of reference audio. GPU recommended.

```python
# pip install TTS
from TTS.api import TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")
tts.tts_to_file(text="Hello!", speaker_wav="my_voice.wav", language="en", file_path="out.wav")
```

## Recommendation
- **Demo / free:** Piper TTS (offline) or OpenAI TTS (if key present).
- **Best human-like + cloning (PDF's "preferred"):** ElevenLabs free tier, or Coqui
  XTTS if you must self-host. See [VOICE_CLONING.md](VOICE_CLONING.md).
