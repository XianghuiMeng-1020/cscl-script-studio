#!/usr/bin/env bash
# Phase B smoke: login -> upload -> list -> preflight -> generate
# Usage: BASE_URL=http://localhost:5001 ./scripts/smoke_prod_flow.sh
# Output: PASS or FAIL with reason. Exit 0 only if all steps pass.
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:5001}"
API="${BASE_URL}/api"
CSCL="${API}/cscl"
COURSE_ID="default-course"

# Credentials: use T001/teacher123 (conftest) or teacher_demo/demo (seed_demo_users.py)
USER_ID="${SMOKE_USER:-T001}"
PASSWORD="${SMOKE_PASSWORD:-teacher123}"

COOKIE_JAR=$(mktemp)
trap 'rm -f "$COOKIE_JAR"' EXIT

fail() { echo "FAIL: $*"; exit 1; }
ok()   { echo "  OK: $*"; }

echo "=============================================="
echo "Smoke: login -> upload -> list -> preflight -> generate"
echo "BASE_URL=$BASE_URL  COURSE_ID=$COURSE_ID"
echo "=============================================="

# 1. Login
echo ""
echo "1. Login (POST $API/auth/login)"
LOGIN_RESP=$(curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" -X POST -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"password\":\"$PASSWORD\"}" "$API/auth/login" 2>/dev/null) || true
if ! echo "$LOGIN_RESP" | grep -qE '"message"|"user"'; then
  fail "Login failed or no session. Response: ${LOGIN_RESP:0:200}"
fi
ok "login"

# 2. Upload (text document)
echo ""
echo "2. Upload doc (POST $CSCL/courses/$COURSE_ID/docs/upload)"
UPLOAD_RESP=$(curl -sf -b "$COOKIE_JAR" -X POST -H "Content-Type: application/json" \
  -d '{"title":"Smoke Doc","text":"This is a smoke test document. It has enough content to pass the minimum length requirement for upload (at least 80 characters)."}' \
  "$CSCL/courses/$COURSE_ID/docs/upload" 2>/dev/null) || true
if ! echo "$UPLOAD_RESP" | grep -qE '"success":\s*true|"ok":\s*true'; then
  fail "Upload failed. Response: ${UPLOAD_RESP:0:300}"
fi
ok "upload"

# 3. List docs
echo ""
echo "3. List docs (GET $CSCL/courses/$COURSE_ID/docs)"
LIST_RESP=$(curl -sf -b "$COOKIE_JAR" "$CSCL/courses/$COURSE_ID/docs" 2>/dev/null) || true
if ! echo "$LIST_RESP" | grep -q '"success":\s*true'; then
  fail "List docs failed. Response: ${LIST_RESP:0:200}"
fi
if echo "$LIST_RESP" | grep -q '"documents"'; then
  ok "list documents"
else
  fail "List response missing documents key"
fi

# 4. Create script (same course_id for B1)
echo ""
echo "4. Create script (POST $CSCL/scripts)"
SCRIPT_RESP=$(curl -sf -b "$COOKIE_JAR" -X POST -H "Content-Type: application/json" \
  -d "{\"title\":\"Smoke Script\",\"topic\":\"ML\",\"course_id\":\"$COURSE_ID\",\"task_type\":\"structured_debate\",\"duration_minutes\":90}" \
  "$CSCL/scripts" 2>/dev/null) || true
SCRIPT_ID=$(echo "$SCRIPT_RESP" | grep -o '"id":"[^"]*"' | head -1 | sed 's/"id":"//;s/"//')
if [ -z "$SCRIPT_ID" ]; then
  fail "Create script failed. Response: ${SCRIPT_RESP:0:300}"
fi
ok "create script ($SCRIPT_ID)"

# 5. Preflight (POST .../pipeline/preflight)
echo ""
echo "5. Preflight (POST $CSCL/scripts/$SCRIPT_ID/pipeline/preflight)"
SPEC='{
  "course_context": {"subject":"DS","topic":"ML","class_size":30,"mode":"sync","duration":90,"description":"Smoke test course context."},
  "learning_objectives": {"knowledge":["K1"],"skills":["S1"]},
  "task_requirements": {"task_type":"structured_debate","expected_output":"Report","collaboration_form":"group","requirements_text":"Minimal requirements for smoke."}
}'
PREFLIGHT_RESP=$(curl -sf -b "$COOKIE_JAR" -X POST -H "Content-Type: application/json" \
  -d "{\"spec\":$SPEC}" "$CSCL/scripts/$SCRIPT_ID/pipeline/preflight" 2>/dev/null) || true
if ! echo "$PREFLIGHT_RESP" | grep -qE '"ready":\s*true|"success":\s*true'; then
  # Preflight can fail with 503 if provider not ready; that's acceptable for smoke (we checked endpoint works)
  if echo "$PREFLIGHT_RESP" | grep -q '"error_code":\s*"LLM_PROVIDER_NOT_READY"'; then
    ok "preflight (endpoint OK, provider not ready)"
  else
    fail "Preflight failed. Response: ${PREFLIGHT_RESP:0:400}"
  fi
else
  ok "preflight"
fi

# 6. Generate (pipeline/run) - may 503 if no LLM
echo ""
echo "6. Pipeline run (POST $CSCL/scripts/$SCRIPT_ID/pipeline/run)"
RUN_RESP=$(curl -sf -b "$COOKIE_JAR" -X POST -H "Content-Type: application/json" \
  -H "Idempotency-Key: smoke-$(date +%s)" \
  -d "{\"spec\":$SPEC}" "$CSCL/scripts/$SCRIPT_ID/pipeline/run" 2>/dev/null) || true
if echo "$RUN_RESP" | grep -qE '"success":\s*true.*"run_id"|"run_id"'; then
  ok "pipeline run"
elif echo "$RUN_RESP" | grep -q '"code":\s*"LLM_PROVIDER_NOT_READY"'; then
  ok "pipeline run (endpoint OK, provider not ready - 503)"
else
  fail "Pipeline run failed. Response: ${RUN_RESP:0:400}"
fi

echo ""
echo "=============================================="
echo "PASS"
echo "=============================================="
exit 0
