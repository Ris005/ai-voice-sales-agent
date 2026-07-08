# 🎙️ Voice & Audio Documentation

This folder explains **what the assignment PDF asks for on voice quality**, **why the
current build sounds robotic**, and **exactly how to upgrade to a human-like AI voice**
using the free/open-source tools the PDF suggests.

## Why this exists
The current app uses the browser's built-in **Web Speech API** (`speechSynthesis`) for
audio. It works everywhere with zero setup, but the voices are OS-default and sound
robotic — which is the audio-quality problem you noticed. The assignment explicitly
wants a **human-like AI voice (voice cloning preferred)**, so these docs lay out the
upgrade path.

## Read in this order

| # | Doc | What it covers |
|---|-----|----------------|
| 1 | [VOICE_REQUIREMENTS.md](VOICE_REQUIREMENTS.md) | Exactly what the PDF asks for on voice, mapped to status |
| 2 | [AUDIO_QUALITY.md](AUDIO_QUALITY.md) | Why the current audio is robotic + quick wins vs. real fixes |
| 3 | [TTS_OPTIONS.md](TTS_OPTIONS.md) | Text-to-Speech engines compared (browser, Piper, Coqui, ElevenLabs, OpenAI) |
| 4 | [STT_OPTIONS.md](STT_OPTIONS.md) | Speech-to-Text options (browser, Whisper, faster-whisper) |
| 5 | [VOICE_CLONING.md](VOICE_CLONING.md) | How to clone a specific voice (the PDF's "preferred") |
| 6 | [VOICE_PIPELINE.md](VOICE_PIPELINE.md) | Full real-time pipeline: LiveKit / Pipecat + telephony |
| 7 | [UPGRADE_PLAN.md](UPGRADE_PLAN.md) | Step-by-step: swap browser TTS → server TTS in this codebase |

## TL;DR — three tiers of audio quality

| Tier | Setup | Quality | Cost |
|------|-------|---------|------|
| **A. Browser TTS** (current) | none | 🟠 robotic | free |
| **B. Server neural TTS** (OpenAI TTS / Piper) | small | 🟢 natural | free–cheap |
| **C. Cloned voice + streaming** (ElevenLabs / Coqui XTTS) | medium | 🟢🟢 human, custom | free tier / self-host |

The fastest jump in quality is **Tier B with OpenAI TTS** — one endpoint, one env var,
and it plays MP3 in the browser instead of the robotic system voice. See
[UPGRADE_PLAN.md](UPGRADE_PLAN.md).
