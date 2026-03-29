<div align="center">

# claude-voice

**Hands-free voice I/O for Claude Code — speak naturally, hear responses.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey?style=for-the-badge)](#)
[![Groq](https://img.shields.io/badge/Groq-Whisper_STT-F55036?style=for-the-badge)](https://console.groq.com)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=for-the-badge)](LICENSE)

<img src="demo.gif" alt="Voice daemon detecting wake word, transcribing speech, sending to Claude Code" width="700">

</div>

---

Typing context into Claude interrupts thinking. Sometimes you just want to talk through a problem and hear an answer back — hands free, screen optional.

## Install

One command. Takes 30 seconds.

```bash
curl -fsSL https://raw.githubusercontent.com/nardovibecoding/claude-voice/main/install.sh | bash
```

Installs dependencies, prompts for Groq API key, configures TTS hook in `~/.claude/settings.json`.

<details>
<summary>Manual install</summary>

```bash
git clone https://github.com/nardovibecoding/claude-voice.git
cd claude-voice
pip install groq sounddevice numpy pynput rumps
export GROQ_API_KEY="your-key-here"
```

</details>

## Run

```bash
# Terminal 1 — start voice daemon
python voice_daemon.py

# Terminal 2 — start Claude Code as normal
claude
```

**Or wire it into your shell so it auto-starts with Claude:**

```bash
# ~/.zshrc
claude() {
    python ~/claude-voice/voice_daemon.py &
    command claude "$@"
    kill %1 2>/dev/null
}
```

---

## How It Works

```
You speak
    │
    ▼
VAD detects speech (RMS > 0.10)
    │
    ▼
Records until 1.5s silence
    │
    ├── < 0.8s? → Discard (noise rejection)
    │
    ▼
Groq Whisper STT (whisper-large-v3-turbo)
    │
    ▼
Auto-typed into Claude Code terminal
    │
    ▼
Claude responds → macOS TTS reads it aloud (say)
```

---

## Features

| Feature | Details |
|---|---|
| **VAD Auto-Detect** | Energy-based voice activity detection — starts recording when you speak, stops after 1.5s silence |
| **Groq Whisper STT** | Fast cloud transcription via `whisper-large-v3-turbo`, supports Chinese and English |
| **Noise Rejection** | Recordings under 0.8s are silently discarded — no wasted API calls |
| **macOS TTS Output** | Claude's responses spoken aloud via the `say` command (Sinji voice, 220 wpm) |
| **Menubar Indicator** | Live status icon: idle / recording / transcribing / muted |
| **Mute Toggle** | One keypress mutes TTS without stopping the daemon |
| **Manual Push-to-Talk** | Hold Right Option key to record instead of VAD, for noisy environments |
| **Mode Switching** | Toggle between VAD auto, manual push-to-talk, and wake word at any time |
| **Wake Word** | "Hey Claude" hands-free activation via openWakeWord — optional dependency |
| **Linux Support** | Cross-platform via xdotool, pyperclip, mpv, pystray — replaces macOS-only components |
| **Single-Instance Lock** | Starting the daemon auto-kills any previous instance — no zombie processes |

---

## Requirements

| Requirement | Notes |
|---|---|
| macOS 14+ | Uses `say` for TTS and macOS Accessibility API for keystroke injection |
| Python 3.11+ | Tested on 3.11 and 3.12 |
| Groq API key | Free tier available at [console.groq.com](https://console.groq.com) — generous limits |
| Microphone | External mic recommended for cleaner VAD detection |
| Accessibility permission | Required for global hotkeys and auto-typing transcription |
| Input Monitoring permission | Required for key detection (Right Option, Right Cmd, etc.) |

macOS will prompt for permissions on first run.

---

## Controls

| Key | Action |
|---|---|
| **Right Option** | Hold to record in manual push-to-talk mode |
| **Right Shift** | Cycle mode: OFF → VAD → WAKE_WORD → OFF |
| **Left Shift** | Cancel current recording |
| **Left Alt / Left Cmd** | Interrupt TTS playback immediately |
| **Right Cmd** | Toggle mute on/off |

---

## Menubar Indicator

| Icon | State |
|---|---|
| `🟢` | VAD standby — listening for speech |
| `⌥` | Manual mode — hold Right Option to record |
| `🔴` | Recording in progress |
| `🟡` | Transcribing — request sent to Groq |
| `🔇` | Muted (prefixed on any state) |

---

## Wake Word

Say **"Hey Claude"** to trigger recording hands-free — no keypress needed.

```bash
pip install openwakeword
WAKE_WORD=true python voice_daemon.py
```

openWakeWord is an optional dependency. When `WAKE_WORD=false` (default), the daemon uses VAD auto-detect or manual push-to-talk. Right Shift cycles through all three modes: OFF → VAD → WAKE_WORD → OFF.

---

## Linux Support

All macOS-specific components have Linux equivalents:

| macOS component | Linux replacement |
|---|---|
| `say` command (TTS) | `mpv` + Edge TTS |
| macOS Accessibility API (keystroke injection) | `xdotool type` |
| `pynput` global hotkeys | `pynput` (works on X11/Wayland) |
| `rumps` menubar app | `pystray` system tray |
| Clipboard paste | `pyperclip` |

Install on Linux:

```bash
sudo apt install xdotool mpv
pip install groq sounddevice numpy pynput pystray pyperclip
```

---

## Configuration

All settings are environment variables — no config file needed.

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(required)* | Groq API key for Whisper transcription |
| `STT_ENGINE` | `groq` | STT backend: `groq`, `google`, `apple`, or `whisper` (local) |
| `STT_LANGUAGE` | *(empty)* | Force transcription language (e.g. `zh`, `en`). Empty = auto-detect |
| `TTS_VOICE` | `zh-HK-HiuMaanNeural` | Edge TTS voice name for spoken responses |
| `TTS_RATE` | `+0%` | Speech rate adjustment (e.g. `+20%`, `-10%`) |
| `WAKE_WORD` | `false` | Enable `true` to activate "Hey Claude" hands-free mode (requires openWakeWord) |
| `VAD_ENERGY_THRESHOLD` | `0.10` | RMS threshold for speech detection — raise in noisy environments |
| `VAD_SILENCE_TIMEOUT_FRAMES` | `50` | Frames of silence before stopping (~1.5s at default chunk size) |
| `MIN_RECORDING_CHUNKS` | `27` | Minimum recording length (~0.8s) — shorter clips are discarded |
| `PREFERRED_MIC` | `External Microphone` | Substring match against input device names |

---

## File Structure

```
claude-voice/
├── voice_daemon.py          # Core: VAD loop, STT, keyboard injection (540 lines)
├── speak_hook.py            # TTS: Claude Code stop-hook — speaks the last response
├── recording_indicator.py   # Menubar: rumps app showing live recording state
└── toggle_mute.sh           # Helper: toggle /tmp/tts_muted flag file
```

**`speak_hook.py`** is designed to run as a Claude Code [stop hook](https://docs.anthropic.com/en/docs/claude-code/hooks) — it fires automatically after each Claude response and reads it aloud.

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=nardovibecoding/claude-voice&type=Date)](https://star-history.com/#nardovibecoding/claude-voice&Date)

---

## License

[AGPL-3.0](LICENSE) — see LICENSE for full terms.
