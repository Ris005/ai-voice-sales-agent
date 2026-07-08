# 4 · Speech-to-Text (STT) Options

The engine that turns the prospect's speech into text for the agent. The PDF suggests
**Whisper**.

## Comparison

| Engine | Accuracy | Cost | Runs | Streaming | PDF-listed |
|--------|:-------:|:----:|:----:|:--------:|:----------:|
| Browser `SpeechRecognition` (current) | 🟢 | free | client (Chrome/Edge) | ✅ | — |
| **OpenAI Whisper** (local) | 🟢🟢 | free | CPU/GPU | ❌ (chunked) | ✅ |
| **faster-whisper** | 🟢🟢 | free | CPU/GPU (fast) | ~chunked | ✅ (Whisper) |
| **OpenAI Whisper API** | 🟢🟢 | cheap | API | ❌ | ✅ (OpenAI API) |
| **Deepgram / AssemblyAI** | 🟢🟢🟢 | paid | API | ✅ real-time | — |

## Current
The browser's `SpeechRecognition` already transcribes the prospect in Chrome/Edge and
feeds text to `/api/call/turn`. It is good and free but browser-only.

## Whisper (PDF-suggested) — server-side, portable
```bash
pip install openai-whisper        # or: pip install faster-whisper
```

```python
# app/stt.py
import whisper
model = whisper.load_model("base")   # tiny/base/small/medium/large

def transcribe(wav_path: str) -> str:
    return model.transcribe(wav_path)["text"].strip()
```

`faster-whisper` (CTranslate2) is 4–5× faster on CPU with the same accuracy:
```python
from faster_whisper import WhisperModel
model = WhisperModel("base", device="cpu", compute_type="int8")
segments, _ = model.transcribe("clip.wav")
text = " ".join(s.text for s in segments)
```

## OpenAI Whisper API (if key present)
```python
from openai import OpenAI
client = OpenAI()
with open("clip.wav", "rb") as f:
    text = client.audio.transcriptions.create(model="whisper-1", file=f).text
```

## When to move off the browser STT
- You need **real-time streaming** with barge-in → Deepgram/AssemblyAI or the
  streaming ASR built into LiveKit/Pipecat (see [VOICE_PIPELINE.md](VOICE_PIPELINE.md)).
- You need **non-Chrome browsers** or **server-side** transcription → Whisper.
