# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Desktop transcription app for Windows that captures **microphone** and **system audio** (WASAPI loopback) simultaneously and transcribes both streams to text using Whisper locally. Primary use case: transcribing calls (Zoom, Teams, etc.) in Spanish.

## Tech Stack

- **Python 3.10+** — main language
- **faster-whisper** — local Whisper transcription (CTranslate2-based, faster than original)
- **pyaudiowpatch** — WASAPI loopback capture (system audio on Windows)
- **sounddevice** — microphone capture
- **customtkinter** — UI
- **numpy** — audio buffer handling
- **CUDA (RTX 3050)** — GPU acceleration for transcription

## Architecture

Two independent audio capture threads feed 4-second chunks into a shared transcription queue. A third thread processes the queue with `faster-whisper` and emits results to the UI.

```
Mic thread (sounddevice)      ─┐
                                ├─► AudioBuffer (4s chunks) ─► TranscriptionWorker ─► UI
Loopback thread (pyaudiowpatch) ┘        (numpy)               (faster-whisper CUDA)
```

Key design decisions:
- Audio sources are labeled (`[MIC]` / `[SISTEMA]`) and written to a single transcript log
- Model: `medium` with `int8` quantization, `language="es"` fixed to avoid detection overhead
- Chunks overlap slightly to avoid cutting words at boundaries

## Commands

### Setup

```bash
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
```

### Run the app

```bash
python main.py
```

### Install CUDA-enabled faster-whisper

```bash
pip install faster-whisper
# CUDA 12: pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

## File Structure (planned)

```
main.py              # Entry point, launches UI
transcriber/
  audio_capture.py   # Mic and loopback capture threads
  transcription.py   # faster-whisper worker
  buffer.py          # Audio chunk buffering logic
ui/
  app.py             # customtkinter main window
requirements.txt
```

## Key Notes

- WASAPI loopback requires `pyaudiowpatch` (not standard `pyaudio`). It captures whatever is playing through the default output device.
- faster-whisper device should be `"cuda"` with `compute_type="int8_float16"` for RTX 3050.
- If CUDA is unavailable, fall back to `device="cpu"` and `compute_type="int8"`.
- The model file (~800MB for medium int8) is downloaded automatically on first run to `~/.cache/huggingface/`.
