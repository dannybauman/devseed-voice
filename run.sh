#!/bin/sh
# Start a separate Foley for this agent: its own home, port and profile, local to this Mac
set -e
DIR=$(cd "$(dirname "$0")" && pwd)
[ -f "$DIR/.env.local" ] && . "$DIR/.env.local"
[ -f "$DIR/notebooks.json" ] || { echo "copy notebooks.example.json to notebooks.json first"; exit 1; }
FOLEY_DIR=${FOLEY_DIR:-$HOME/Source/claude-skills/foley-service}
export FOLEY_HOME=${FOLEY_HOME:-$HOME/.foley-devseed}
export FOLEY_PORT=${FOLEY_PORT:-50141}
export NLM_PROFILE=${NLM_PROFILE:-devseed}
mkdir -p "$FOLEY_HOME"
python3 - "$DIR" "$FOLEY_HOME/profile.yaml" <<'EOF'
import json, sys
d, out = sys.argv[1], sys.argv[2]
nbs = json.load(open(f"{d}/notebooks.json"))
names = "; ".join(f'"{k}" ({v["about"]})' for k, v in nbs.items())
text = open(f"{d}/profile.yaml").read().replace("{{NOTEBOOKS}}", names)
open(out, "w").write(text.replace("~/Source/devseed-voice", d))
EOF
# never inherit a key from this shell: it may be a personal one that bills the wrong account
unset GEMINI_API_KEY
[ -n "$KEY_CMD" ] && GEMINI_API_KEY=$(sh -c "$KEY_CMD") && export GEMINI_API_KEY
[ -n "$GEMINI_API_KEY" ] || { echo "no Gemini key: set KEY_CMD in .env.local"; exit 1; }
# Tailscale access is off unless DEVSEED_TAILSCALE_LOGIN names who may reach it
export FOLEY_TAILSCALE_LOGIN=${DEVSEED_TAILSCALE_LOGIN:-}
echo "DevSeed voice: http://127.0.0.1:$FOLEY_PORT/"
cd "$FOLEY_DIR"
exec "${FOLEY_PY:-$FOLEY_DIR/.venv/bin/python}" server.py
