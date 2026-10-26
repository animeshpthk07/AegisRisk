#!/usr/bin/env bash
set -Eeuo pipefail

# This image cannot be switched into a shared, persistent deployment by env.
if [[ "${SYNTHETIC_IMPORTS_ENABLED:-false}" != "false" ]]; then
  echo "Demo refuses persistent imports; use the authenticated deployment instead." >&2
  exit 64
fi
export SYNTHETIC_IMPORTS_ENABLED=false
export DATABASE_URL=sqlite:////tmp/aegisrisk-demo/fictional.db
export API_BASE_URL=http://127.0.0.1:8000
export HOSTNAME=127.0.0.1
export PORT="${PORT:-10000}"
if [[ ! "$PORT" =~ ^[0-9]{4,5}$ ]] || (( PORT < 1024 || PORT > 65535 )); then
  echo "PORT must be an unprivileged TCP port." >&2
  exit 64
fi
mkdir -p /tmp/aegisrisk-demo /tmp/aegisrisk-nginx
sed "s/__PORT__/$PORT/g" /app/demo/nginx.conf > /tmp/aegisrisk-nginx/nginx.conf
nginx -t -c /tmp/aegisrisk-nginx/nginx.conf
cd /app/api
alembic upgrade head
python -m aegisrisk.seed

pids=()
cleanup() {
  trap - EXIT TERM INT
  if (( ${#pids[@]} )); then
    kill -TERM "${pids[@]}" 2>/dev/null || true
    wait "${pids[@]}" 2>/dev/null || true
  fi
}
trap cleanup EXIT
trap 'exit 0' TERM INT
# Bind both application servers to loopback; only nginx accepts external traffic.
python -m uvicorn aegisrisk.main:app --host 127.0.0.1 --port 8000 --no-access-log --limit-concurrency 12 --timeout-keep-alive 5 &
pids+=("$!")
PORT=3000 node /app/web/apps/web/server.js &
pids+=("$!")
nginx -c /tmp/aegisrisk-nginx/nginx.conf -g 'daemon off;' &
pids+=("$!")
# Any child exit terminates the others, allowing the host to restart cleanly.
set +e
wait -n "${pids[@]}"
status=$?
set -e
if (( status == 0 )); then status=1; fi
exit "$status"
