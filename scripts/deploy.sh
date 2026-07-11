#!/bin/bash
# ---------------------------------------------------------------------------
# Deploy local changes to the OPARLI production server (oparli.com).
# Bypasses GitHub (server has no git auth) — copies files directly over SSH.
#
# Usage:  ./scripts/deploy.sh            # frontend + backend + restart
#         ./scripts/deploy.sh frontend   # only rebuild+push the website
#         ./scripts/deploy.sh backend    # only push backend code + restart API
# ---------------------------------------------------------------------------
set -e

KEY=~/.ssh/oracle_new_key
SRV=root@46.225.218.50
APP=/opt/oparli

cd "$(dirname "$0")/.."          # repo root
WHAT="${1:-all}"

if [ "$WHAT" = "all" ] || [ "$WHAT" = "frontend" ]; then
  echo "==> Building frontend..."
  ( cd frontend && npm run build )
  echo "==> Uploading website to nginx root..."
  rsync -az --delete -e "ssh -i $KEY" frontend/dist/ "$SRV:$APP/frontend/dist/"
fi

if [ "$WHAT" = "all" ] || [ "$WHAT" = "backend" ]; then
  echo "==> Uploading backend code (skips venv / .env / caches)..."
  rsync -az \
    --exclude 'venv/' --exclude '.env' --exclude '__pycache__/' --exclude '*.pyc' \
    -e "ssh -i $KEY" backend/ "$SRV:$APP/backend/"
  echo "==> Restarting API..."
  ssh -i "$KEY" "$SRV" "systemctl restart oparli-api && sleep 2 && systemctl is-active oparli-api"
fi

echo "==> Done. Hard-refresh the browser (Cmd+Shift+R) to clear cached JS."
