#!/usr/bin/env bash
# Wait for IB Gateway's API port to accept connections before starting the
# scanner. The gateway container takes ~1-2 min to launch + log in; without this
# the scanner would crash-loop against a closed port. Combined with the
# compose restart policy, a mid-session gateway restart is also ridden out.
set -euo pipefail

HOST="${IB_HOST:-ibgateway}"
PORT="${IB_PORT:-4002}"

echo "entrypoint: waiting for IB Gateway API at ${HOST}:${PORT} ..."
for i in $(seq 1 120); do
  if python -c "import socket,sys; s=socket.socket(); s.settimeout(2); sys.exit(0 if s.connect_ex(('${HOST}',${PORT}))==0 else 1)"; then
    echo "entrypoint: gateway port open, giving it 10s to finish login"; sleep 10
    break
  fi
  sleep 5
done

exec python /app/deterministic_scanner.py --live
