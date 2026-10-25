#!/bin/sh
# Stop the voice agent that up.sh started and take down its phone path
DIR=$(cd "$(dirname "$0")" && pwd)
[ -f "$DIR/.env.local" ] && . "$DIR/.env.local"
HOME_DIR=${FOLEY_HOME:-$HOME/.foley-devseed}
PID_FILE="$HOME_DIR/server.pid"
if [ -f "$PID_FILE" ] && ps -o command= -p "$(cat "$PID_FILE")" | grep -q server.py; then
  kill "$(cat "$PID_FILE")"
fi
rm -f "$PID_FILE"
if [ -n "$DEVSEED_TAILSCALE_LOGIN" ] && command -v tailscale >/dev/null; then
  tailscale serve --https=443 --set-path /devseed-voice off >/dev/null 2>&1 || true
fi
echo "stopped"
