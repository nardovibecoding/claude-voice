# Copyright (c) 2026 Nardo. AGPL-3.0 — see LICENSE
#!/usr/bin/env python3
"""
Claude Code Stop hook — reads assistant response from stdin and speaks it.
Checks /tmp/tts_muted IMMEDIATELY before speaking. No background races.
"""

import sys
import json
import re
import subprocess
import os

IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform == "linux"

EDGE_VOICE = os.environ.get("TTS_VOICE", "zh-HK-HiuMaanNeural")
EDGE_RATE = os.environ.get("TTS_RATE", "+0%")
MAX_CHARS = 300
MUTE_FLAG = "/tmp/tts_muted"
SPEAK_PID_FILE = "/tmp/speak_hook_bg.pid"


def clean_text(text):
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*+([^*]+)\*+", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\|[^\n]+\|", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "……"
    return text


def speak(text):
    # Kill any previous TTS process
    if IS_LINUX:
        subprocess.run(["pkill", "-f", "mpv"], capture_output=True)
    else:
        subprocess.run(["pkill", "-x", "say"], capture_output=True)
    try:
        old_pid = int(open(SPEAK_PID_FILE).read())
        os.kill(old_pid, 9)
    except Exception:
        pass

    # Background script — edge-tts generates mp3, platform player plays it
    _play_cmd = '["mpv", "--no-video", mp3]' if IS_LINUX else '["afplay", mp3]'
    script = f"""
import time, os, subprocess, sys, asyncio

my_pid = os.getpid()
open({repr(SPEAK_PID_FILE)}, "w").write(str(my_pid))

# Wait for any active recording/transcription to finish
for _ in range(60):
    if not os.path.exists("/tmp/recording_active") and not os.path.exists("/tmp/transcribing_active"):
        break
    time.sleep(0.1)

# Check we are still the active speak process
try:
    current = int(open({repr(SPEAK_PID_FILE)}).read())
except Exception:
    current = None
if current != my_pid:
    sys.exit(0)

# Final mute check — RIGHT before speaking, no gap
if os.path.exists({repr(MUTE_FLAG)}):
    sys.exit(0)

async def _speak():
    import edge_tts
    mp3 = "/tmp/tts_output.mp3"
    communicate = edge_tts.Communicate({repr(text)}, "{EDGE_VOICE}", rate="{EDGE_RATE}")
    await communicate.save(mp3)
    subprocess.run({_play_cmd})
    try:
        os.unlink(mp3)
    except Exception:
        pass

asyncio.run(_speak())
"""
    subprocess.Popen(["python3", "-c", script])


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
        text = data.get("last_assistant_message", "")

        # Debug log EVERY invocation
        muted = os.path.exists(MUTE_FLAG)
        with open("/tmp/speak_hook_debug.log", "a") as f:
            import time as _t
            f.write(f"{_t.strftime('%H:%M:%S')} muted={muted} text_len={len(text)} text={text[:50]!r}\n")

        # First gate: check mute before doing anything
        if muted:
            return

        if text:
            text = clean_text(text)
            if text:
                speak(text)

    except Exception as e:
        with open("/tmp/speak_hook_error.log", "a") as f:
            f.write(f"{e}\n{raw[:200] if 'raw' in dir() else ''}\n---\n")


if __name__ == "__main__":
    main()
