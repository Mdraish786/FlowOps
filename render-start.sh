#!/bin/sh
set -eu

# Apply database migrations before the web server starts.
alembic upgrade head

# Optional demo seed. It is safe on restarts: an existing workspace is left alone.
if [ "${SEED_DEMO:-false}" = "true" ]; then
  python -m app.render_seed
fi

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-10000}" \
  --proxy-headers \
  --forwarded-allow-ips='*'
