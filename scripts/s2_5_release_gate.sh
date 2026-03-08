#!/bin/bash
# S2.5 FINAL RELEASE GATE - 全绿才允许标记“可部署”
# 每项检查输出 PASS/FAIL; 任一失败脚本退出非0

set -uo pipefail

BASE_URL="${BASE_URL:-http://localhost:5001}"
API_BASE="${BASE_URL}/api"
# Support both bash and sh: use $0 so cd works when script is run as ./scripts/s2_5_release_gate.sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

PASS=0
FAIL=0

check() {
    local name="$1"
    shift
    echo -n "  $name... "
    if "$@" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((PASS++)) || true
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((FAIL++)) || true
        return 1
    fi
}

# Allow check failures to not exit script (we count FAIL and exit at end)
set +e

echo "=============================================="
echo "S2.5 RELEASE GATE"
echo "=============================================="

# 1. health 200 + status=ok
echo ""
echo "1. Health 200 + status=ok"
check "health 200" curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/api/health" | grep -q 200
check "health status=ok" curl -sf "$BASE_URL/api/health" | grep -q '"status":"ok"'

# 2. / /teacher /student 可达 (S2.12: 未登录时 /teacher /student 可 302 到 /login)
echo ""
echo "2. Pages reachable"
check "/ 200" curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/" | grep -q 200
CODE_T=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/teacher" 2>/dev/null || echo "000")
if [ "$CODE_T" = "200" ] || [ "$CODE_T" = "302" ]; then
    echo -e "  /teacher $CODE_T... ${GREEN}PASS${NC}"
    ((PASS++)) || true
else
    echo -e "  /teacher $CODE_T (expect 200 or 302)... ${RED}FAIL${NC}"
    ((FAIL++)) || true
fi
CODE_S=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/student" 2>/dev/null || echo "000")
if [ "$CODE_S" = "200" ] || [ "$CODE_S" = "302" ]; then
    echo -e "  /student $CODE_S... ${GREEN}PASS${NC}"
    ((PASS++)) || true
else
    echo -e "  /student $CODE_S (expect 200 or 302)... ${RED}FAIL${NC}"
    ((FAIL++)) || true
fi

# 3. 认证拦截 /api/cscl/scripts 返回 401 或 403（未登录或无权限）
echo ""
echo "3. Auth: /api/cscl/scripts returns 401 or 403 when unauthenticated"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/cscl/scripts" 2>/dev/null || echo "000")
if [ "$CODE" = "401" ] || [ "$CODE" = "403" ]; then
    echo -e "  Auth intercept (got $CODE)... ${GREEN}PASS${NC}"
    ((PASS++)) || true
else
    echo -e "  Auth intercept (got $CODE, expect 401/403)... ${RED}FAIL${NC}"
    ((FAIL++)) || true
fi

# 4. 三语关键文案存在（三页面）
echo ""
echo "4. i18n key coverage (3 pages)"
check "index home.teacher.card" grep -q 'data-i18n="home.teacher.card"' templates/index.html
check "teacher teacher.sidebar.spec" grep -q 'data-i18n="teacher.sidebar.spec"' templates/teacher.html
check "student student.title" grep -q 'data-i18n="student.title"' templates/student.html
check "i18n zh-CN zh-TW en" grep -q "'zh-CN':" static/js/i18n.js && grep -q "'zh-TW':" static/js/i18n.js && grep -q "'en':" static/js/i18n.js
check "app_locale" grep -q "app_locale" static/js/i18n.js

# 5. UI 术语 Spec 在可见文案归零（data-i18n 和静态文案中不用 “Spec” 作显示文本）
echo ""
echo "5. UI term 'Spec' zero in visible copy"
if grep -E 'data-i18n="[^"]*[Ss]pec[^"]*"' templates/*.html static/js/i18n.js 2>/dev/null | grep -v 'teacher.sidebar.spec\|teacher.spec\.\|spec_why\|spec_hash\|spec_validat' | grep -q .; then
    echo -e "  Spec in i18n keys (review)... ${RED}FAIL${NC}"
    ((FAIL++)) || true
else
    echo -e "  No raw 'Spec' in visible UI keys... ${GREEN}PASS${NC}"
    ((PASS++)) || true
fi
check "No Pedagogical specifications in teacher" sh -c '! grep -q "Pedagogical specifications" templates/teacher.html'

# 6. teacher 9 菜单与 9 视图映射
echo ""
echo "6. Teacher 9 menu + 9 view mapping"
check "9 nav items" sh -c "cd '$PROJECT_ROOT' && test \$(grep -c 'data-view=' templates/teacher.html 2>/dev/null || echo 0) -ge 9"
check "9+ view containers" sh -c "cd '$PROJECT_ROOT' && test \$(grep -c 'class=.view.' templates/teacher.html 2>/dev/null || echo 0) -ge 9"
check "teacher.js viewNameToId or switchView" grep -q "switchView\|viewNameToId" "$PROJECT_ROOT/static/js/teacher.js"
check "dashboard menu" grep -q 'data-view="dashboard"' "$PROJECT_ROOT/templates/teacher.html"
check "settings menu" grep -q 'data-view="settings"' "$PROJECT_ROOT/templates/teacher.html"

# 7. student 空状态与活动态可解释
echo ""
echo "7. Student empty state + error copy"
check "student.empty.title in i18n" grep -q "student.empty.title" static/js/i18n.js
check "student.error.login in i18n" grep -q "student.error.login" static/js/i18n.js
check "showEmptyState in student.js" grep -q "showEmptyState" static/js/student.js

# 8. PDF 提取接口污染检测（文档服务返回 preview 不含 %PDF- xref obj stream）
echo ""
echo "8. PDF extraction guardrails"
check "document_service PDF_PARSE_FAILED" grep -q "PDF_PARSE_FAILED" app/services/document_service.py
check "extracted_text_preview in upload response" grep -q "extracted_text_preview\|extraction_metadata" app/services/document_service.py
check "normalize_text + binary markers" grep -q "_PDF_BINARY_MARKERS\|normalize_text" app/services/document_service.py

# 9. 关键 API 链路 smoke（validate/create/run/quality/export 至少存在路由）
echo ""
echo "9. Key API routes exist"
check "POST /api/cscl/spec/validate" grep -q "spec/validate" app/routes/cscl.py
check "POST /api/cscl/scripts" grep -q "@.*route.*scripts.*POST\|def create_script" app/routes/cscl.py
check "pipeline run" grep -q "pipeline\|run" app/routes/cscl.py
check "quality" grep -q "quality" app/routes/cscl.py
check "export" grep -q "export" app/routes/cscl.py

# 10. 错误码路径返回用户友好消息（API 返回 code 或 error，非裸堆栈）
echo ""
echo "10. Error codes user-friendly"
check "health returns JSON" curl -sf "$BASE_URL/api/health" | grep -q "status"
check "cscl error has code/error" sh -c "curl -s -X POST -H 'Content-Type: application/json' -d '{}' '$BASE_URL/api/cscl/spec/validate' 2>/dev/null | grep -qE '\"code\"|\"error\"|\"valid\"'"

# 11. provider 字段可观察
echo ""
echo "11. Provider field observable"
check "health has provider" curl -sf "$BASE_URL/api/health" | grep -q '"provider"'

echo ""
echo "=============================================="
echo "TOTAL: $PASS passed, $FAIL failed"
echo "=============================================="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
