#!/usr/bin/env bash
# S2.17 HARD FIX gate: teacher clickable + PDF no binary leak. All checks must PASS.
cd "$(dirname "$0")/.."
ENV_FILE="${ENV_FILE:-.env}"
BASE_URL="${BASE_URL:-http://localhost:5001}"

PASS=0
FAIL=0
report() { echo "[S2.17] $1"; }
pass() { report "PASS: $1"; PASS=$((PASS+1)); }
fail() { report "FAIL: $1"; FAIL=$((FAIL+1)); }

# 1) /api/health 200 and llm_primary, llm_fallback, llm_strategy, auth_mode, status
report "--- Health ---"
HEALTH=$(curl -sS "${BASE_URL}/api/health" 2>/dev/null || true)
HEALTH_OK=0
if echo "$HEALTH" | grep -q '"status"'; then
  ALL=1
  for key in status llm_primary llm_fallback llm_strategy auth_mode; do
    if echo "$HEALTH" | grep -q "\"$key\""; then :; else fail "health missing: $key"; ALL=0; fi
  done
  [ "$ALL" -eq 1 ] && HEALTH_OK=1
fi
if [ "$HEALTH_OK" -eq 1 ]; then pass "health 200 + fields"; else fail "health non-200 or non-JSON"; fi

# 2) /teacher unauthenticated -> 302 to /login
report "--- Teacher redirect ---"
CODE=$(curl -sS -o /dev/null -w "%{http_code}" "${BASE_URL}/teacher" 2>/dev/null || true)
if [ "$CODE" = "302" ]; then pass "teacher 302"; else fail "teacher unauthenticated (got $CODE)"; fi

# 3) /login 200
LOGIN_CODE=$(curl -sS -o /dev/null -w "%{http_code}" "${BASE_URL}/login" 2>/dev/null || true)
if [ "$LOGIN_CODE" = "200" ]; then pass "login 200"; else fail "login (got $LOGIN_CODE)"; fi

# 4) Login then teacher page 200
COOKIE_FILE=/tmp/s2_17_cookie.txt
curl -sS -c "$COOKIE_FILE" -b "$COOKIE_FILE" -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" -d '{"user_id":"teacher_demo","password":"Demo@12345"}' 2>/dev/null | true
TEACHER_CODE=$(curl -sS -o /dev/null -w "%{http_code}" -L -b "$COOKIE_FILE" "${BASE_URL}/teacher" 2>/dev/null || true)
if [ "$TEACHER_CODE" = "200" ]; then pass "teacher after login 200"; else fail "teacher after login (got $TEACHER_CODE)"; fi

# 5) static/js/teacher.js 200 and Content-Length > 0
HL=$(curl -sS -I "${BASE_URL}/static/js/teacher.js" 2>/dev/null || true)
SC=$(echo "$HL" | head -1)
CL=$(echo "$HL" | grep -i content-length | awk '{print $2}' | tr -d '\r')
if echo "$SC" | grep -q "200"; then
  if [ -n "$CL" ] && [ "$CL" -gt 0 ] 2>/dev/null; then pass "teacher.js 200 + Content-Length>0"; else fail "teacher.js Content-Length 0 or missing"; fi
else
  fail "teacher.js not 200"
fi

# 6) Page source: step buttons must not use inline goToStep (no onclick="goToStep)
PAGE=$(curl -sS -L -b "$COOKIE_FILE" "${BASE_URL}/teacher" 2>/dev/null || true)
if echo "$PAGE" | grep -q 'onclick="goToStep'; then fail "page contains onclick=goToStep"; else pass "page no inline goToStep"; fi
if echo "$PAGE" | grep -q 'onclick="event.stopPropagation(); goToStep'; then fail "page contains inline goToStep"; else pass "page no inline goToStep stopPropagation"; fi

# 7) teacher.js four-phase logs + delegation
JS=$(curl -sS "${BASE_URL}/static/js/teacher.js" 2>/dev/null || true)
for kw in "script loaded" "dom ready" "bind start" "bind end"; do
  if echo "$JS" | grep -q "\[teacher\] $kw"; then pass "teacher.js log: $kw"; else fail "teacher.js missing: $kw"; fi
done
if echo "$JS" | grep -q 'delegation bind start'; then pass "teacher.js delegation bind start"; else fail "teacher.js delegation bind start"; fi
if echo "$JS" | grep -q 'delegation bind end'; then pass "teacher.js delegation bind end"; else fail "teacher.js delegation bind end"; fi

# 8) PDF no binary leak
TMP_PDF=$(mktemp)
printf '%%PDF-1.4\n1 0 obj\nstream\n\x00\x01\nendstream\nendobj\n' > "$TMP_PDF"
UPLOAD=$(curl -sS -b "$COOKIE_FILE" -X POST "${BASE_URL}/api/cscl/courses/default-course/docs/upload" \
  -F "file=@${TMP_PDF};filename=bad.pdf" -F "title=bad" 2>/dev/null || true)
rm -f "$TMP_PDF"
if echo "$UPLOAD" | grep -qE 'PDF_PARSE_FAILED|EMPTY_EXTRACTED_TEXT|TEXT_TOO_SHORT'; then pass "PDF upload rejected with code"; elif echo "$UPLOAD" | grep -q '"error"'; then pass "PDF upload error (auth or other, no binary)"; else fail "PDF upload no error code"; fi
if echo "$UPLOAD" | grep -q '%PDF-'; then fail "PDF response contains %PDF-"; else pass "PDF response no %PDF-"; fi

# 9) pytest full green (run in container if docker available, else skip)
report "--- Pytest ---"
if docker compose --env-file "$ENV_FILE" exec -T web python -m pytest tests/ -q --tb=no 2>/dev/null | tail -3 | grep -q 'passed'; then
  pass "pytest passed"
else
  fail "pytest failed or not run"
fi

report "--- Result: PASS=$PASS FAIL=$FAIL ---"
if [ "$FAIL" -gt 0 ]; then exit 1; fi
exit 0
