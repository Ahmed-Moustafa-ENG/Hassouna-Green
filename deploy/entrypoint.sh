#!/bin/sh
# Start Hassouna Green.
#
# Writes Streamlit's own configuration from the DOMAIN environment variable,
# so the same image works for any domain, then starts the app.
set -eu

DOMAIN="${DOMAIN:-}"
CONFIG_DIR="${STREAMLIT_CONFIG_DIR:-/config}"
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$CONFIG_DIR" "$APP_DIR/.streamlit"

# The port and the address are set in the image; the domain decides which
# hostnames and origins the app answers to.
cat > "$APP_DIR/.streamlit/config.toml" <<EOF
[server]
headless = true
address = "0.0.0.0"
port = 8501
# The proxy in front of the app passes the same origin, so the browser only
# ever talks to this one domain.
enableCORS = false
enableXsrfProtection = true
EOF

if [ -n "$DOMAIN" ]; then
	cat >> "$APP_DIR/.streamlit/config.toml" <<EOF
allowedHosts = ["$DOMAIN", "www.$DOMAIN", "localhost", "127.0.0.1"]
EOF
	echo "Hassouna Green is configured for $DOMAIN"
else
	cat >> "$APP_DIR/.streamlit/config.toml" <<EOF
allowedHosts = ["localhost", "127.0.0.1"]
EOF
	echo "WARNING: DOMAIN is not set. The app only answers to localhost." >&2
fi

cd "$APP_DIR"
exec python -m streamlit run 22_updated.py
