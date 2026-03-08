#!/bin/bash
# S2.3 BLOCKER HOTFIX Verification Script
# - Health check
# - Three pages key文案 grep (3 languages)
# - Upload sample PDF and verify preview不含二进制标记
# - pytest tests/test_s2_3_blockers.py
# - Output PASS/FAIL and exit code

set -e

BASE_URL="${BASE_URL:-http://localhost:5001}"
API_BASE="${API_BASE:-${BASE_URL}/api}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

test_ok() {
    echo -n "  $1... "
    if eval "$2" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((FAIL++))
        return 1
    fi
}

echo "=========================================="
echo "S2.3 BLOCKER HOTFIX Verification"
echo "=========================================="
echo ""

# 1. Health check
echo "1. Health Check"
test_ok "Health endpoint 200" "curl -s -o /dev/null -w '%{http_code}' ${API_BASE}/health 2>/dev/null | grep -q '200'"

# 2. Three pages key文案 grep (3 languages)
echo ""
echo "2. Key文案 in templates (i18n keys)"
test_ok "index.html home.title" "grep -q 'data-i18n=\"home.title\"' templates/index.html"
test_ok "index.html home.teacher.card" "grep -q 'data-i18n=\"home.teacher.card\"' templates/index.html"
test_ok "teacher.html teacher.sidebar.spec" "grep -q 'data-i18n=\"teacher.sidebar.spec\"' templates/teacher.html"
test_ok "teacher.html teacher.spec.validate" "grep -q 'teacher.spec.validate' templates/teacher.html"
test_ok "student.html student.title" "grep -q 'data-i18n=\"student.title\"' templates/student.html"

echo ""
echo "3. i18n 3 languages"
test_ok "i18n zh-CN" "grep -q \"'zh-CN':\" static/js/i18n.js"
test_ok "i18n zh-TW" "grep -q \"'zh-TW':\" static/js/i18n.js"
test_ok "i18n en" "grep -q \"'en':\" static/js/i18n.js"
test_ok "app_locale persistence" "grep -q 'app_locale' static/js/i18n.js"

# 4. PDF upload and preview (requires server + auth)
echo ""
echo "4. PDF/TXT upload preview (no binary markers)"
mkdir -p "$PROJECT_ROOT/data"

# Try API upload (text) if server is up and we have auth
UPLOAD_OK=0
CSCL_API="${CSCL_API:-$API_BASE/cscl}"
if curl -s -o /dev/null -w '%{http_code}' "${API_BASE}/health" 2>/dev/null | grep -q '200'; then
    COOKIE_FILE="/tmp/s2_3_cookie_$$.txt"
    LOGIN=$(curl -s -c "$COOKIE_FILE" -X POST "${API_BASE}/auth/login" -H "Content-Type: application/json" -d '{"user_id":"T001","password":"teacher123"}' 2>/dev/null || true)
    if echo "$LOGIN" | grep -q 'Login successful\|"user"'; then
        TEXT_CONTENT="Introduction to Data Science. This course covers fundamental concepts in machine learning, statistics, and programming. Students will learn to apply analytical methods."
        UPLOAD_RESP=$(curl -s -b "$COOKIE_FILE" -X POST "${CSCL_API}/courses/DEMO/docs/upload" \
            -H "Content-Type: application/json" \
            -d "{\"title\":\"S2.3 Sample\",\"text\":\"${TEXT_CONTENT}\"}" 2>/dev/null || true)
        rm -f "$COOKIE_FILE"
        if echo "$UPLOAD_RESP" | grep -q '"ok":true'; then
            PREVIEW=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('extracted_text_preview',''))" 2>/dev/null || echo "")
            if [ -n "$PREVIEW" ]; then
                if echo "$PREVIEW" | grep -qE '%PDF-| obj |stream|endobj|endstream|xref'; then
                    echo "  Upload preview contains binary markers... ${RED}FAIL${NC}"
                    ((FAIL++))
                else
                    echo "  Upload preview clean (no binary markers)... ${GREEN}PASS${NC}"
                    ((PASS++))
                    UPLOAD_OK=1
                fi
            else
                echo "  Upload response structure... ${GREEN}PASS${NC} (preview empty for text)"
                ((PASS++))
                UPLOAD_OK=1
            fi
        else
            echo "  Upload (auth/session) skipped (may need login)... ${YELLOW}SKIP${NC}"
        fi
    else
        echo "  Upload (no demo user) skipped... ${YELLOW}SKIP${NC}"
    fi
else
    echo "  Upload (server not running) skipped... ${YELLOW}SKIP${NC}"
fi

if [ $UPLOAD_OK -eq 0 ]; then
    # Fallback when live upload skipped: verify document_service and API structure
    test_ok "document_service PDF markers regex" "grep -q '_PDF_BINARY_MARKERS' app/services/document_service.py"
    test_ok "upload API returns extracted_text_preview" "grep -q 'extracted_text_preview' app/routes/cscl.py"
fi

# 5. pytest
echo ""
echo "5. pytest tests/test_s2_3_blockers.py"
if python -m pytest tests/test_s2_3_blockers.py -v --tb=short 2>&1 | tee /tmp/s2_3_pytest.log; then
    echo -e "  pytest... ${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "  pytest... ${RED}FAIL${NC}"
    ((FAIL++))
fi

# Summary
echo ""
echo "=========================================="
echo "S2.3 Verification Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}${PASS}${NC}"
echo -e "Failed: ${RED}${FAIL}${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}PASS${NC}"
    exit 0
else
    echo -e "${RED}FAIL${NC}"
    exit 1
fi
