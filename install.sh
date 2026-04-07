#!/usr/bin/env bash
# Claude Voice — one-liner installer
# curl -fsSL https://raw.githubusercontent.com/nardovibecoding/claude-voice/main/install.sh | bash
set -euo pipefail

INSTALL_DIR="$HOME/claude-voice"
SETTINGS="$HOME/.claude/settings.json"

RED='\033[0;31m' GREEN='\033[0;32m' YELLOW='\033[1;33m' CYAN='\033[0;36m' BOLD='\033[1m' NC='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}"
echo "  ╔═══════════════════════════════════╗"
echo "  ║   Claude Voice Installer           ║"
echo "  ║   TTS + STT for Claude Code        ║"
echo "  ╚═══════════════════════════════════╝"
echo -e "${NC}"

# --- Check Python ---
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}✗ Python 3 is required. Install it first.${NC}"
  exit 1
fi

# --- Clone or update ---
if [ -d "$INSTALL_DIR/.git" ]; then
  echo -e "${YELLOW}→ Updating existing install...${NC}"
  git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null || true
else
  if [ -d "$INSTALL_DIR" ]; then
    echo -e "${RED}✗ $INSTALL_DIR exists but is not a git repo. Remove it first.${NC}"
    exit 1
  fi
  echo -e "${GREEN}→ Cloning repository...${NC}"
  git clone https://github.com/nardovibecoding/claude-voice.git "$INSTALL_DIR"
fi

# --- Install dependencies ---
echo -e "${GREEN}→ Installing Python dependencies...${NC}"
pip3 install --quiet groq sounddevice numpy pynput 2>/dev/null || {
  echo -e "${YELLOW}  Some packages failed. Trying individually...${NC}"
  for pkg in groq sounddevice numpy pynput; do
    pip3 install --quiet "$pkg" 2>/dev/null || echo -e "${RED}  ✗ Failed to install $pkg${NC}"
  done
}

# macOS menu bar indicator
if [[ "$(uname)" == "Darwin" ]]; then
  pip3 install --quiet rumps 2>/dev/null || true
fi

# --- API Key ---
echo ""
read -rp "Groq API key (for STT, get one at console.groq.com): " GROQ_KEY
if [ -n "$GROQ_KEY" ]; then
  # Save to shell profile
  PROFILE="$HOME/.zshrc"
  [ -f "$HOME/.bash_profile" ] && PROFILE="$HOME/.bash_profile"
  if ! grep -q "GROQ_API_KEY" "$PROFILE" 2>/dev/null; then
    echo "export GROQ_API_KEY=\"$GROQ_KEY\"" >> "$PROFILE"
    echo -e "  ${GREEN}Added GROQ_API_KEY to $PROFILE${NC}"
  fi
  export GROQ_API_KEY="$GROQ_KEY"
fi

# --- Configure Claude Code TTS hook ---
echo -e "${GREEN}→ Configuring TTS hook...${NC}"
mkdir -p "$HOME/.claude"

python3 << 'PYEOF'
import json, os

INSTALL_DIR = os.path.expanduser("~/claude-voice")
SETTINGS = os.path.expanduser("~/.claude/settings.json")

if os.path.exists(SETTINGS):
    with open(SETTINGS) as f:
        settings = json.load(f)
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
MARKER = "claude-voice"

# TTS hook fires after every Claude response
stop_hooks = hooks.setdefault("Stop", [])
stop_hooks[:] = [h for h in stop_hooks if not any(MARKER in hook.get("command", "") for hook in h.get("hooks", []))]
stop_hooks.append({
    "matcher": "",
    "hooks": [{"type": "command", "command": f"python3 {INSTALL_DIR}/speak_hook.py", "timeout": 10000}]
})

with open(SETTINGS, "w") as f:
    json.dump(settings, f, indent=2)

print("  TTS hook configured in ~/.claude/settings.json")
PYEOF

# --- Done ---
echo ""
echo -e "${GREEN}${BOLD}✓ Claude Voice installed!${NC}"
echo ""
echo -e "  ${BOLD}TTS${NC}: Claude speaks responses aloud (automatic via Stop hook)"
echo -e "  ${BOLD}STT${NC}: Hold a key to dictate instead of typing"
echo -e "  ${BOLD}Indicator${NC}: Menubar icon auto-launches with the daemon"
echo ""
echo -e "  To start everything (daemon + indicator):"
echo -e "    ${CYAN}python3 ~/claude-voice/voice_daemon.py${NC}"
echo ""
echo -e "  ${YELLOW}Restart Claude Code if it's already running.${NC}"
echo ""
