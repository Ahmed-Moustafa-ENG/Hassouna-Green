#!/usr/bin/env bash
# Build and run Hassouna Green on this server.
#
#   cd deploy
#   cp .env.example .env      # then set DOMAIN
#   ./deploy.sh
#
# After this, the app answers on https://your-domain.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
	echo "No deploy/.env found. Copy .env.example to .env and set DOMAIN." >&2
	exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
	echo "Docker is not installed. See DEPLOY.md, step 3." >&2
	exit 1
fi

echo "Building and starting..."
docker compose up -d --build

echo
echo "Waiting for the app to come up..."
for i in $(seq 1 30); do
	if docker compose exec -T app python -c \
		"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)" 2>/dev/null; then
		echo "The app is up."
		break
	fi
	sleep 2
done

echo
echo "  site:  https://$(grep '^DOMAIN=' .env | cut -d= -f2)"
echo "  logs:  cd deploy && docker compose logs -f app"
echo "  stop:  cd deploy && docker compose down"
