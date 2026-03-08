#!/usr/bin/env bash
# S2.15 HARD-GATE: verifiable delivery only. All checks must PASS.
set -e
cd "$(dirname "$0")/.."
ENV_FILE="${ENV_FILE:-.env}"
BASE_URL="${BASE_URL:-http://localhost:5001}"

PASS=0
FAIL=0
report() { echo "[S2.15] $1"; }
pass() { report "PASS: $1"; PASS=$((PASS+1)); }
fail() { report "FAIL: $1"; FAIL=$((FAIL+1)); }

# 1) Health: status, llm_primary, llm_fallback, llm_strategy, auth_mode
report "--- Health check ---"
HEALTH=$(curl -sS "${BASE_URL}/api/health" 2>/dev/null || true)
if echo "$HEALTH" | grep -q '"status"'; then
  for key in status llm_primary llm_fallback llm_strategy auth_mode; do
    if echo "$HEALTH" | grep -q "\"$key\""; then :; else fail "health missing field: $key"; fi
  done
  if [ "$FAIL" -eq 0 ]; then pass "health check (fields present)"; fi
else
  fail "health check (curl or non-JSON)"
fi

# 2) /teacher unauthenticated -> 302 to /login
report "--- Teacher redirect ---"
REDIR=$(curl -sS -o /dev/null -w "%{http_code}|%{redirect_url}" -L -c /tmp/s2_15_cj -b /tmp/s2_15_cj "${BASE_URL}/teacher" 2>/dev/null || true)
CODE=$(echo "$REDIR" | cut -d'|' -f1)
if [ "$CODE" = "302" ] || [ "$CODE" = "200" ]; then
  FIRST=$(curl -sS -o /dev/null -w "%{http_code}" -c /tmp/s2_15_cj -b /tmp/s2_15_cj "${BASE_URL}/teacher" 2>/dev/null || true)
  if [ "$FIRST" = "302" ]; then pass "teacher unauthenticated 302"; else fail "teacher unauthenticated (got $FIRST)"; fi
else
  fail "teacher redirect (got $CODE)"
fi

# 3) /login 200
report "--- Login page ---"
LOGIN_CODE=$(curl -sS -o /dev/null -w "%{http_code}" "${BASE_URL}/login" 2>/dev/null || true)
if [ "$LOGIN_CODE" = "200" ]; then pass "login page 200"; else fail "login page (got $LOGIN_CODE)"; fi

# 4) Teacher static: teacher.js, student.js, i18n.js 200 and Content-Length > 0
report "--- Teacher static resources ---"
for res in /static/js/teacher.js /static/js/student.js /static/js/i18n.js; do
  HL=$(curl -sS -I "${BASE_URL}${res}" 2>/dev/null || true)
  SC=$(echo "$HL" | head -1)
  CL=$(echo "$HL" | grep -i content-length | awk '{print $2}' | tr -d '\r')
  if echo "$SC" | grep -q "200"; then
    if [ -n "$CL" ] && [ "$CL" -gt 0 ] 2>/dev/null; then pass "static $res 200 + Content-Length>0"; else fail "static $res Content-Length missing or 0"; fi
  else
    fail "static $res (not 200)"
  fi
done

# 5) Teacher page contains bind start/end and data-action buttons (HTML source)
report "--- Teacher page DOM (after login) ---"
# Login first
COOKIE_FILE=/tmp/s2_15_cookie.txt
curl -sS -c "$COOKIE_FILE" -b "$COOKIE_FILE" -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" -d '{"user_id":"teacher_demo","password":"Demo@12345"}' 2>/dev/null | true
PAGE=$(curl -sS -L -b "$COOKIE_FILE" "${BASE_URL}/teacher" 2>/dev/null || true)
if echo "$PAGE" | grep -q 'data-action="import-outline"'; then pass "teacher DOM data-action import-outline"; else fail "teacher DOM missing data-action import-outline"; fi
if echo "$PAGE" | grep -q 'data-action="validate-goals"'; then pass "teacher DOM data-action validate-goals"; else fail "teacher DOM missing data-action validate-goals"; fi
if echo "$PAGE" | grep -q 'data-action="run-pipeline"'; then pass "teacher DOM data-action run-pipeline"; else fail "teacher DOM missing data-action run-pipeline"; fi
JS=$(curl -sS "${BASE_URL}/static/js/teacher.js" 2>/dev/null || true)
if echo "$JS" | grep -q '\[teacher\] script loaded'; then pass "teacher script loaded log"; else fail "teacher script loaded"; fi
if echo "$JS" | grep -q '\[teacher\] dom ready'; then pass "teacher dom ready log"; else fail "teacher dom ready"; fi
if echo "$JS" | grep -q '\[teacher\] bind start'; then pass "teacher bind start log"; else fail "teacher bind start"; fi
if echo "$JS" | grep -q '\[teacher\] bind end'; then pass "teacher bind end log"; else fail "teacher bind end"; fi

# 6) PDF no binary leak: upload garbage PDF -> 422 + code PDF_PARSE_FAILED or no %PDF in response
report "--- PDF no binary leak ---"
# Create minimal garbage PDF bytes
TMP_PDF=$(mktemp)
printf '%%PDF-1.4\n1 0 obj\nstream\n\x00\x01\nendstream\nendobj\n' > "$TMP_PDF"
UPLOAD=$(curl -sS -b "$COOKIE_FILE" -X POST "${BASE_URL}/api/cscl/courses/default-course/docs/upload" \
  -F "file=@${TMP_PDF};filename=bad.pdf" -F "title=bad" 2>/dev/null || true)
rm -f "$TMP_PDF"
if echo "$UPLOAD" | grep -q 'PDF_PARSE_FAILED'; then pass "PDF upload returns PDF_PARSE_FAILED"; else
  # May be 422 with code in JSON
  if echo "$UPLOAD" | grep -q '"code"'; then pass "PDF upload returns error code"; else fail "PDF upload binary leak check (no PDF_PARSE_FAILED or code)"; fi
fi
if echo "$UPLOAD" | grep -q '%PDF-'; then fail "PDF response must not contain %PDF-"; else pass "PDF response no %PDF- in body"; fi

report "--- Result: PASS=$PASS FAIL=$FAIL ---"
if [ "$FAIL" -gt 0 ]; then exit 1; fi
exit 0
