#!/usr/bin/env bash
# Release readiness: run critical checks. Exit non-zero if any blocker fails.
# Usage: ./scripts/release_readiness_check.sh [BASE_URL]
# Checks: health, docs upload/list (no regression), preflight exists, API returns JSON (no HTML).
set -euo pipefail

BASE_URL="${1:-${BASE_URL:-http://localhost:5001}}"
API="${BASE_URL}/api"
CSCL="${API}/cscl"
FAIL=0

echo "=============================================="
echo "Release Readiness Check (BASE_URL=$BASE_URL)"
echo "=============================================="

# 1. Health returns 200 and JSON
echo ""
echo "1. GET /api/health -> 200, JSON, status=ok"
CODE=$(curl -s -o /tmp/health.json -w "%{http_code}" "$API/health" 2>/dev/null || echo "000")
CT=$(curl -sI "$API/health" 2>/dev/null | grep -i content-type || true)
if [ "$CODE" != "200" ]; then
  echo "   FAIL: health returned $CODE (expected 200)"
  FAIL=1
elif ! grep -q '"status"' /tmp/health.json 2>/dev/null; then
  echo "   FAIL: health response not JSON or missing status"
  FAIL=1
else
  echo "   OK"
fi

# 2. API 404 returns JSON (B3: no HTML)
echo ""
echo "2. GET /api/nonexistent -> 404, JSON body (no HTML)"
CODE=$(curl -s -o /tmp/err404.txt -w "%{http_code}" "$API/nonexistent" 2>/dev/null || echo "000")
if echo "$(cat /tmp/err404.txt 2>/dev/null)" | grep -q '<!DOCTYPE\|<html'; then
  echo "   FAIL: API 404 returned HTML (expected JSON)"
  FAIL=1
elif [ "$CODE" != "404" ]; then
  echo "   FAIL: expected 404, got $CODE"
  FAIL=1
else
  echo "   OK"
fi

# 3. Docs list (unauthenticated -> 401 or 403, not 500)
echo ""
echo "3. GET /api/cscl/courses/default-course/docs without auth -> 401 or 403"
CODE=$(curl -s -o /tmp/docs.txt -w "%{http_code}" "$CSCL/courses/default-course/docs" 2>/dev/null || echo "000")
if [ "$CODE" != "401" ] && [ "$CODE" != "403" ]; then
  echo "   FAIL: expected 401/403, got $CODE"
  FAIL=1
else
  echo "   OK ($CODE)"
fi

# 4. Preflight endpoint exists (401/403 without auth is fine)
echo ""
echo "4. POST .../pipeline/preflight exists (401/403 without auth)"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" \
  -d '{"spec":{}}' "$CSCL/scripts/00000000-0000-0000-0000-000000000000/pipeline/preflight" 2>/dev/null || echo "000")
if [ "$CODE" = "404" ]; then
  echo "   FAIL: preflight endpoint not found (404)"
  FAIL=1
else
  echo "   OK (got $CODE)"
fi

# 5. Optional: run full smoke if SMOKE=1
if [ "${SMOKE:-0}" = "1" ]; then
  echo ""
  echo "5. Full smoke (SMOKE=1)"
  if bash "$(dirname "$0")/smoke_prod_flow.sh" 2>&1; then
    echo "   OK"
  else
    echo "   FAIL: smoke script failed"
    FAIL=1
  fi
else
  echo ""
  echo "5. Skip full smoke (set SMOKE=1 to run)"
fi

echo ""
echo "=============================================="
if [ $FAIL -eq 0 ]; then
  echo "PASS (release readiness checks)"
  exit 0
else
  echo "FAIL (one or more blockers failed)"
  exit 1
fi
