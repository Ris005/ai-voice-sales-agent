# 6 · Full Real-Time Voice Pipeline

For **natural flow, pauses, and interruption handling** (barge-in) — and for **real
outbound phone calls** — you need a streaming media pipeline instead of the turn-based
request/response the app uses today. The PDF suggests **LiveKit Agents or Pipecat**.

## Turn-based (today) vs. streaming (goal)

```
TODAY (turn-based):
  prospect speaks → STT (whole utterance) → LLM → TTS (whole reply) → play
  Simple, but no interruption; the agent can't be cut off mid-sentence.

GOAL (streaming):
  mic ──▶ VAD ──▶ streaming STT ──▶ LLM (streamed) ──▶ streaming TTS ──▶ speaker
                     ▲                                                     │
                     └───────────── barge-in: stop TTS on speech ─────────┘
```

- **VAD** (voice activity detection, e.g. Silero) detects when the prospect starts
  talking and lets the agent **stop speaking** — real interruption handling.
- Streaming STT + streaming TTS keep latency < ~1s so it feels like a real call.

## Option A — Pipecat (Python, open-source)
Composable pipeline of frames (audio in → STT → LLM → TTS → audio out). Good fit since
this app is already Python.

```python
# sketch — pipecat pipeline
from pipecat.pipeline.pipeline import Pipeline
from pipecat.services.whisper import WhisperSTTService
from pipecat.services.openai import OpenAILLMService
from pipecat.services.elevenlabs import ElevenLabsTTSService

pipeline = Pipeline([
    transport.input(),          # mic / phone audio in
    WhisperSTTService(),        # speech → text
    OpenAILLMService(model="gpt-4o-mini", system_prompt=SALES_PROMPT),
    ElevenLabsTTSService(voice_id=VOICE_ID),   # text → speech (cloned)
    transport.output(),         # audio out
])
```
Reuse this app's `agent.py` sales logic as the LLM system prompt + knowledge base, and
call the existing CRM write on call end.

## Option B — LiveKit Agents (WebRTC + telephony)
LiveKit gives you WebRTC rooms and **SIP/telephony** for real PSTN calls, with an Agents
framework that wires STT/LLM/TTS and handles interruption out of the box.

```python
# sketch — livekit agents
from livekit.agents import VoicePipelineAgent
from livekit.plugins import openai, silero, elevenlabs

agent = VoicePipelineAgent(
    vad=silero.VAD.load(),
    stt=openai.STT(),                      # or Whisper/Deepgram
    llm=openai.LLM(model="gpt-4o-mini"),
    tts=elevenlabs.TTS(voice=VOICE_ID),    # cloned voice
)
```

## Real outbound phone calls (PSTN)
The browser call is a simulation. For actual phone dialing:

| Provider | Role |
|----------|------|
| **Twilio** (Programmable Voice / SIP) | buys a number, dials the lead, streams audio |
| **LiveKit SIP** | bridges the call into the LiveKit/agent pipeline |
| **Plivo / Telnyx** | alternatives to Twilio |

Flow: Twilio dials the lead → media streamed into Pipecat/LiveKit → agent talks →
on hangup, write the outcome to the Excel CRM exactly as the app does now.

## What stays the same
The **sales brain (`app/agent.py`)**, **knowledge base**, and **Excel CRM
(`app/crm.py`)** are transport-agnostic — you reuse them unchanged. Only the audio
transport swaps from "browser turn-based" to "streaming pipeline + telephony".
