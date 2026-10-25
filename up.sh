#!/bin/sh
# Start the voice agent in the background and print where to open it.
# With DEVSEED_TAILSCALE_LOGIN set in .env.local it is also mounted for that login's phone
# at https://<this machine>.ts.net/devseed-voice/ (a path, since phones may not reach extra ports)
set -e
DIR=$(cd "$(dirname "$0")" && pwd)
[ -f "$DIR/.env.local" ] && . "$DIR/.env.local"
HOME_DIR=${FOLEY_HOME:-$HOME/.foley-devseed}
PORT=${FOLEY_PORT:-50141}
mkdir -p "$HOME_DIR"
if ! curl -s -m 2 -o /dev/null "http://127.0.0.1:$PORT/"; then
  nohup "$DIR/run.sh" > "$HOME_DIR/server.log" 2>&1 &
  echo $! > "$HOME_DIR/server.pid"
  for i in $(seq 1 60); do curl -s -m 2 -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.5; done
fi
curl -s -m 2 -o /dev/null "http://127.0.0.1:$PORT/" || { echo "did not start, see $HOME_DIR/server.log"; exit 1; }
echo "local: http://127.0.0.1:$PORT/"
if [ -n "$DEVSEED_TAILSCALE_LOGIN" ] && command -v tailscale >/dev/null; then
  tailscale serve --bg --set-path /devseed-voice "http://127.0.0.1:$PORT" >/dev/null
  host=$(tailscale status --self --json | python3 -c "import sys,json;print(json.load(sys.stdin)['Self']['DNSName'].rstrip('.'))")
  echo "phone: https://$host/devseed-voice/"
fi
