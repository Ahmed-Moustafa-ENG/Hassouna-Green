#!/usr/bin/env bash
# Start Hassouna Green and give it a public address, free and without a domain.
#
#   ./deploy/tunnel.sh
#
# The app keeps running on this machine; cloudflared only lends it a public
# HTTPS address. The address changes every time you start it again.
#
# Keep this terminal open. Ctrl+C stops both.
set -euo pipefail

cd "$(dirname "$0")/.."
PORT=8501
CF=deploy/cloudflared

if [ ! -x "$CF" ]; then
	echo "Downloading cloudflared (the tunnel client)..."
	curl -fsSL -o "$CF" \
		https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
	chmod +x "$CF"
fi

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
echo "Your app is online at:"
echo
exec "$CF" tunnel --url "http://127.0.0.1:$PORT" --no-autoupdate
