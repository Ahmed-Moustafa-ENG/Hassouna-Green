#!/usr/bin/env bash
# Start Hassouna Green on your own domain, from your own computer.
#
#   ./deploy/tunnel-domain.sh
#
# This needs the domain to be on Cloudflare (the DNS is free) and a named
# tunnel, which is set up by this script the first time it runs.
#
# The address is then always the same: https://hassounagreen-eg.com
# Keep this terminal open.
set -euo pipefail

cd "$(dirname "$0")/.."
PORT=8501
DOMAIN=hassounagreen-eg.com
TUNNEL=hassouna-green
CF=deploy/cloudflared
CF_DIR="$HOME/.cloudflared"

if [ ! -x "$CF" ]; then
	echo "Downloading cloudflared (the tunnel client)..."
	curl -fsSL -o "$CF" \
		https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
	chmod +x "$CF"
fi

# ── one-time setup: the tunnel and its DNS route ────────────────────────────
if [ ! -f "$CF_DIR/config.yml" ]; then
	echo "Setting up the tunnel for $DOMAIN (only the first time)..."
	mkdir -p "$CF_DIR"

	# 1. sign in to Cloudflare and pick the domain
	"$CF" tunnel login

	# 2. create the tunnel
	"$CF" tunnel create "$TUNNEL"

	# 3. point the domain at the tunnel
	"$CF" tunnel route dns "$TUNNEL" "$DOMAIN"
	"$CF" tunnel route dns "$TUNNEL" "www.$DOMAIN"

	# 4. write the configuration
	TUNNEL_ID=$(ls "$CF_DIR"/*.json | head -n 1 | sed 's|.*/||; s|\.json$||')
	sed -e "s|TUNNEL_ID|$TUNNEL_ID|" \
	    -e "s|CREDENTIALS_FILE|$CF_DIR/$TUNNEL_ID.json|" \
	    deploy/cloudflared.yml > "$CF_DIR/config.yml"

	echo "The tunnel is ready."
fi

# ── the app ─────────────────────────────────────────────────────────────────
if [ ! -x .venv/bin/python ]; then
	echo "No virtual environment found. Run: python3 -m venv .venv" >&2
	echo "and then: .venv/bin/pip install -r requirements.txt" >&2
	exit 1
fi

echo "Starting the app..."
.venv/bin/python -m streamlit run 22_updated.py \
	--server.port "$PORT" --server.address 127.0.0.1 --server.headless true &
APP_PID=$!
trap 'kill $APP_PID 2>/dev/null || true' EXIT

sleep 6
if ! kill -0 "$APP_PID" 2>/dev/null; then
	echo "The app did not start. Run it once by hand to see the error." >&2
	exit 1
fi

echo
echo "Your app is online at: https://$DOMAIN"
echo
exec "$CF" tunnel run "$TUNNEL"
