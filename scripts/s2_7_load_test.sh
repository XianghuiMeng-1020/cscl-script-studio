#!/bin/bash
# S2.7 Minimal Load Test - 20/50 concurrency, 60s each
# Uses curl + xargs (no wrk required)
set -uo pipefail

BASE_URL="${BASE_URL:-http://localhost:5001}"
DURATION="${DURATION:-60}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

run_load() {
  local c="$1"
  local name="$2"
  local url="$3"
  local method="${4:-GET}"
  local body="${5:-}"
  echo "--- $name concurrency=$c duration=${DURATION}s ---"
  local start=$(date +%s)
  local out=$(mktemp)
  trap "rm -f $out" EXIT
  if [ "$method" = "POST" ]; then
    while [ $(($(date +%s) - start)) -lt "$DURATION" ]; do
      seq 1 "$c" | xargs -P "$c" -I {} curl -sf -o /dev/null -w "%{http_code}\n" -X POST -H "Content-Type: application/json" -d "$body" "$url" 2>/dev/null >> "$out" || echo "000" >> "$out"
    done
  else
    while [ $(($(date +%s) - start)) -lt "$DURATION" ]; do
      seq 1 "$c" | xargs -P "$c" -I {} curl -sf -o /dev/null -w "%{http_code}\n" "$url" 2>/dev/null >> "$out" || echo "000" >> "$out"
    done
  fi
  local elapsed=$(($(date +%s) - start))
  local total=0 sum=0
  total=$(grep -c "^2" "$out" 2>/dev/null) || true
  sum=$(wc -l < "$out" 2>/dev/null | tr -d ' \n') || true
  total=${total:-0}
  sum=${sum:-1}
  [ "$sum" -eq 0 ] && sum=1
  local err=$((sum - total))
  local errpct=$((err * 100 / sum))
  echo "  total=$sum err=$err err_pct=${errpct}% elapsed=${elapsed}s"
  echo ""
}

echo "=============================================="
echo "S2.7 LOAD TEST (BASE_URL=$BASE_URL, DURATION=${DURATION}s)"
echo "=============================================="

echo "Read endpoints: /api/health, /, /student"
run_load 20 "health" "$BASE_URL/api/health"
run_load 20 "/" "$BASE_URL/"
run_load 20 "student" "$BASE_URL/student?script_id=test"

echo "Write endpoint: POST /api/cscl/spec/validate"
SPEC='{"course_context":{"subject":"DS","topic":"ML","class_size":30,"mode":"sync","duration":90},"learning_objectives":{"knowledge":["K1"],"skills":["S1"]},"task_requirements":{"task_type":"debate","expected_output":"O","collaboration_form":"group"}}'
run_load 20 "spec/validate" "$BASE_URL/api/cscl/spec/validate" "POST" "$SPEC"

echo "--- Concurrency 50 (health only, 60s) ---"
run_load 50 "health-50" "$BASE_URL/api/health"

echo "DONE. Check err_pct: 5xx≈0 acceptable for classroom use."
