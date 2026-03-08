#!/bin/bash
# Run 20-user concurrent load test: seed DB, start server, run test, stop server.
# Uses SQLite file DB so seed and server share the same data.
set -e
cd "$(dirname "$0")/.."
ROOT="$PWD"
# Use a high port to avoid conflict with other services
PORT=15999
export USE_DB_STORAGE=true
export DATABASE_URL="sqlite:///${ROOT}/data/load_test.db"
export WEB_PORT=$PORT
mkdir -p "${ROOT}/data"

echo "=== Creating tables and seeding 20 users ==="
"${ROOT}/.venv/bin/python" scripts/seed_20_users_load_test.py

echo "=== Starting server in background (requested port $PORT) ==="
LOG=/tmp/cscl_load_test_server_$$.log
"${ROOT}/.venv/bin/python" app.py 2>&1 | tee "$LOG" &
SERVER_PID=$!
trap "kill $SERVER_PID 2>/dev/null || true; rm -f $LOG" EXIT

echo "=== Waiting for server to be ready ==="
sleep 5
# Detect actual port from server log (it may use PORT+1 if PORT was in use)
ACTUAL_PORT=$(grep -m1 "Running on http://127.0.0.1:" "$LOG" 2>/dev/null | sed -n 's/.*:\([0-9]*\)$/\1/p')
if [ -z "$ACTUAL_PORT" ]; then
  ACTUAL_PORT=$PORT
fi
BASE="http://127.0.0.1:${ACTUAL_PORT}"
echo "Using base URL: $BASE"
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/auth/login" -X POST -H "Content-Type: application/json" -d '{"user_id":"x","password":"y"}' 2>/dev/null || echo "000")
  if [ "$CODE" = "401" ] || [ "$CODE" = "200" ]; then
    echo "Server ready (got $CODE)."
    break
  fi
  echo "  try $i: got $CODE"
  sleep 1
done

echo "=== Running 20-user load test (concurrent) ==="
if ! LOAD_TEST_BASE_URL="$BASE" "${ROOT}/.venv/bin/python" scripts/load_test_20_users.py "$BASE"; then
  echo "=== Concurrent test had errors; running sequential mode to verify flow and file handling ==="
  SEQUENTIAL=1 LOAD_TEST_BASE_URL="$BASE" "${ROOT}/.venv/bin/python" scripts/load_test_20_users.py "$BASE"
fi

echo "=== Done ==="
