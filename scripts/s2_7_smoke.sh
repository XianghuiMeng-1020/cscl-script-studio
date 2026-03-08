#!/bin/bash
# S2.7 Post-Deploy Smoke - 上线后自动化冒烟
# BASE_URL 可设为云端地址，如 https://csc.example.com
set -uo pipefail

BASE_URL="${BASE_URL:-http://localhost:5001}"
API_BASE="${BASE_URL}/api"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'
PASS=0 FAIL=0

check() { local n="$1"; shift; echo -n "  $n... "; if "$@" > /dev/null 2>&1; then echo -e "${GREEN}PASS${NC}"; ((PASS++)) || true; return 0; else echo -e "${RED}FAIL${NC}"; ((FAIL++)) || true; return 1; fi; }
set +e

echo "=============================================="
echo "S2.7 SMOKE TEST (BASE_URL=$BASE_URL)"
echo "=============================================="

echo ""
echo "1. Health 200 + status=ok + provider + db_connected"
check "health 200" curl -sf -o /dev/null -w "%{http_code}" "$API_BASE/health" | grep -q 200
check "status=ok" curl -sf "$API_BASE/health" | grep -q '"status":"ok"'
check "provider field" curl -sf "$API_BASE/health" | grep -q '"provider"'
check "db_connected field" curl -sf "$API_BASE/health" | grep -q '"db_connected"'

echo ""
echo "2. Pages reachable"
check "/ 200" curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/" | grep -q 200
check "/teacher 200" curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/teacher" | grep -q 200
check "/student 200" curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/student" | grep -q 200

echo ""
echo "3. Auth: unauthenticated GET /api/cscl/scripts -> 401 or 403"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/cscl/scripts" 2>/dev/null || echo "000")
if [ "$CODE" = "401" ] || [ "$CODE" = "403" ]; then echo -e "  Auth (got $CODE)... ${GREEN}PASS${NC}"; ((PASS++)) || true; else echo -e "  Auth (got $CODE)... ${RED}FAIL${NC}"; ((FAIL++)) || true; fi

echo ""
echo "4. Teacher flow: login -> create script -> validate spec -> quality -> export"
echo "   (Prerequisite: run 'docker compose exec web python scripts/seed_demo_users.py' if first deploy)"
COOKIE_FILE=$(mktemp)
trap "rm -f $COOKIE_FILE" EXIT
LOGIN=$(curl -sf -c "$COOKIE_FILE" -b "$COOKIE_FILE" -X POST -H "Content-Type: application/json" -d '{"user_id":"T001","password":"teacher123"}' "$BASE_URL/api/auth/login" 2>/dev/null)
if echo "$LOGIN" | grep -q "success"; then
  echo -e "  login... ${GREEN}PASS${NC}"
  ((PASS++)) || true
  CREATE=$(curl -sf -b "$COOKIE_FILE" -X POST -H "Content-Type: application/json" -d '{"title":"Smoke","topic":"ML","course_id":"CS101","task_type":"debate","duration_minutes":60}' "$API_BASE/cscl/scripts" 2>/dev/null)
  SID=$(echo "$CREATE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
  if [ -n "$SID" ]; then
    echo -e "  create script... ${GREEN}PASS${NC}"
    ((PASS++)) || true
    VAL=$(curl -sf -b "$COOKIE_FILE" -X POST -H "Content-Type: application/json" -d '{"course_context":{"subject":"DS","topic":"ML","class_size":30,"mode":"sync","duration":90},"learning_objectives":{"knowledge":["K1"],"skills":["S1"]},"task_requirements":{"task_type":"debate","expected_output":"O","collaboration_form":"group"}}' "$API_BASE/cscl/spec/validate" 2>/dev/null)
    if echo "$VAL" | grep -q '"valid"'; then echo -e "  spec validate... ${GREEN}PASS${NC}"; ((PASS++)) || true; else echo -e "  spec validate... ${RED}FAIL${NC}"; ((FAIL++)) || true; fi
    QUAL=$(curl -sf -b "$COOKIE_FILE" "$API_BASE/cscl/scripts/$SID/quality-report" 2>/dev/null)
    if echo "$QUAL" | grep -q "report\|success"; then echo -e "  quality... ${GREEN}PASS${NC}"; ((PASS++)) || true; else echo -e "  quality... ${RED}FAIL${NC}"; ((FAIL++)) || true; fi
    EXP=$(curl -sf -b "$COOKIE_FILE" "$API_BASE/cscl/scripts/$SID/export" 2>/dev/null)
    if echo "$EXP" | grep -q "script\|evidence"; then echo -e "  export... ${GREEN}PASS${NC}"; ((PASS++)) || true; else echo -e "  export... ${RED}FAIL${NC}"; ((FAIL++)) || true; fi
  else
    echo -e "  create script... ${RED}FAIL${NC}"
    ((FAIL++)) || true
  fi
else
  echo -e "  login... ${RED}FAIL${NC}"
  ((FAIL++)) || true
fi

echo ""
echo "5. Student: /student?script_id=xxx returns 200"
check "student page 200" curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/student?script_id=test" | grep -q 200

echo ""
echo "6. PDF guardrails: upload returns extracted_text_preview without binary markers"
# 使用纯文本上传测试（无真实PDF时跳过）
echo -e "  (skipped if no PDF fixture; manual: verify extracted_text_preview no %PDF/obj/stream)"

echo ""
echo "=============================================="
echo "TOTAL: $PASS passed, $FAIL failed"
echo "=============================================="
[ "$FAIL" -gt 0 ] && exit 1
exit 0
