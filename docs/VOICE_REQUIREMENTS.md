# 1 · Voice Requirements (from the Assignment PDF)

This is what the assignment PDF asks for on voice/audio, quoted and mapped to how the
current build meets it.

## What the PDF says

> **AI Voice Calling**
> - Initiate outbound calls.
> - Use a human-like AI voice (**voice cloning preferred**).
> - Maintain natural conversation flow **with pauses and interruption handling**.
> - Introduce the company and purpose of the call.

> **Suggested Free/Open-Source Tools**
> - n8n Community Edition
> - **LiveKit Agents or Pipecat**
> - OpenAI API or Ollama (Llama 3/Qwen)
> - **Whisper** (speech-to-text)
> - **Piper TTS (or ElevenLabs Free Tier)** (text-to-speech)
> - Python (openpyxl/pandas)
> - Supabase (optional)

## Requirement → status in this build

| PDF requirement | Current build | Gap |
|-----------------|---------------|-----|
| Human-like AI voice | Browser `speechSynthesis` (OS voices) | 🟠 Sounds robotic — see [AUDIO_QUALITY.md](AUDIO_QUALITY.md) |
| Voice cloning (preferred) | ❌ not yet | Add ElevenLabs / Coqui XTTS — see [VOICE_CLONING.md](VOICE_CLONING.md) |
| Speech-to-text (listen) | Browser `SpeechRecognition` (Whisper-class) | 🟢 works in Chrome/Edge; swap to Whisper for accuracy/offline |
| Natural flow, pauses | Turn-based (agent speaks, then listens) | 🟡 add streaming + VAD for true interruption handling |
| Interruption handling ("barge-in") | ❌ not yet | Needs streaming pipeline — see [VOICE_PIPELINE.md](VOICE_PIPELINE.md) |
| Introduce company + purpose | 🟢 `agent.opening_line()` | done |
| Initiate outbound calls | Browser call simulation | Real PSTN needs telephony — see [VOICE_PIPELINE.md](VOICE_PIPELINE.md) |

## Key takeaway
The **conversation/CRM logic already satisfies the assignment**. The one weak spot is
**audio realism**, because the browser's default TTS is not neural. Every doc in this
folder is about closing that single gap using the PDF's own suggested tools:
**Piper, ElevenLabs, Whisper, LiveKit/Pipecat.**
