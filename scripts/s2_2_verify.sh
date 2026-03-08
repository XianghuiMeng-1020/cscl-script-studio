#!/bin/bash
# S2.2 Blocking Fix Verification Script
# This script verifies all three blocking fixes:
# 1. i18n language switching
# 2. PDF extraction
# 3. Teacher menu navigation

set -e

BASE_URL="${BASE_URL:-http://localhost:5001}"
API_BASE="${API_BASE:-${BASE_URL}/api}"
CSCL_API="${CSCL_API:-${API_BASE}/cscl}"

echo "=========================================="
echo "S2.2 Blocking Fix Verification"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

# Test function
test_check() {
    local name="$1"
    local command="$2"
    
    echo -n "Testing: $name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((PASS_COUNT++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((FAIL_COUNT++))
        return 1
    fi
}

# 1. Health Check
echo "1. Health Check"
echo "---------------"
test_check "Health endpoint returns 200" \
    "curl -s -o /dev/null -w '%{http_code}' ${API_BASE}/health | grep -q '200'"

# 2. i18n Language Switching
echo ""
echo "2. i18n Language Switching"
echo "---------------------------"

# Check if i18n.js exists
test_check "i18n.js file exists" \
    "test -f static/js/i18n.js"

# Check if language switcher is in HTML files
test_check "Language switcher in index.html" \
    "grep -q 'languageSelect' templates/index.html"

test_check "Language switcher in teacher.html" \
    "grep -q 'languageSelect' templates/teacher.html"

test_check "Language switcher in student.html" \
    "grep -q 'languageSelect' templates/student.html"

# Check i18n dictionary has all three languages
test_check "i18n has zh-CN" \
    "grep -q \"'zh-CN':\" static/js/i18n.js"

test_check "i18n has zh-TW" \
    "grep -q \"'zh-TW':\" static/js/i18n.js"

test_check "i18n has en" \
    "grep -q \"'en':\" static/js/i18n.js"

# 3. PDF Extraction
echo ""
echo "3. PDF Extraction"
echo "------------------"

# Check pypdf in requirements.txt
test_check "pypdf in requirements.txt" \
    "grep -q 'pypdf' requirements.txt"

# Check extract_text_from_pdf function exists
test_check "extract_text_from_pdf function exists" \
    "grep -q 'def extract_text_from_pdf' app/services/document_service.py"

# Check normalize_text function exists
test_check "normalize_text function exists" \
    "grep -q 'def normalize_text' app/services/document_service.py"

# Check PDF is in ALLOWED_EXTENSIONS
test_check "PDF in ALLOWED_EXTENSIONS" \
    "grep -q \"'pdf'\" app/services/document_service.py"

# Check error codes are defined
test_check "PDF_PARSE_FAILED error code" \
    "grep -q 'PDF_PARSE_FAILED' app/services/document_service.py || grep -q 'PDF_PARSE_FAILED' app/routes/cscl.py"

test_check "UNSUPPORTED_FILE_TYPE error code" \
    "grep -q 'UNSUPPORTED_FILE_TYPE' app/services/document_service.py || grep -q 'UNSUPPORTED_FILE_TYPE' app/routes/cscl.py"

test_check "TEXT_TOO_SHORT error code" \
    "grep -q 'TEXT_TOO_SHORT' app/services/document_service.py || grep -q 'TEXT_TOO_SHORT' app/routes/cscl.py"

# Check PDF header removal in normalize_text
test_check "PDF header removal in normalize_text" \
    "grep -q '%PDF-' app/services/document_service.py"

# 4. Teacher Menu Navigation
echo ""
echo "4. Teacher Menu Navigation"
echo "--------------------------"

# Check all menu items have data-view attributes
test_check "Dashboard menu item" \
    "grep -q 'data-view=\"dashboard\"' templates/teacher.html"

test_check "Scripts menu item" \
    "grep -q 'data-view=\"scripts\"' templates/teacher.html"

test_check "Spec validation menu item" \
    "grep -q 'data-view=\"spec-validation\"' templates/teacher.html"

test_check "Pipeline runs menu item" \
    "grep -q 'data-view=\"pipeline-runs\"' templates/teacher.html"

test_check "Documents menu item" \
    "grep -q 'data-view=\"documents\"' templates/teacher.html"

test_check "Decisions menu item" \
    "grep -q 'data-view=\"decisions\"' templates/teacher.html"

test_check "Quality reports menu item" \
    "grep -q 'data-view=\"quality-reports\"' templates/teacher.html"

test_check "Publish menu item" \
    "grep -q 'data-view=\"publish\"' templates/teacher.html"

test_check "Settings menu item" \
    "grep -q 'data-view=\"settings\"' templates/teacher.html"

# Check all views exist in HTML
test_check "dashboardView exists" \
    "grep -q 'id=\"dashboardView\"' templates/teacher.html"

test_check "scriptsView exists" \
    "grep -q 'id=\"scriptsView\"' templates/teacher.html"

test_check "specValidationView exists" \
    "grep -q 'id=\"specValidationView\"' templates/teacher.html"

test_check "pipelineRunsView exists" \
    "grep -q 'id=\"pipelineRunsView\"' templates/teacher.html"

test_check "documentsView exists" \
    "grep -q 'id=\"documentsView\"' templates/teacher.html"

test_check "decisionsView exists" \
    "grep -q 'id=\"decisionsView\"' templates/teacher.html"

test_check "qualityReportsView exists" \
    "grep -q 'id=\"qualityReportsView\"' templates/teacher.html"

test_check "publishView exists" \
    "grep -q 'id=\"publishView\"' templates/teacher.html"

test_check "settingsView exists" \
    "grep -q 'id=\"settingsView\"' templates/teacher.html"

# Check switchView function handles all views
test_check "switchView function exists" \
    "grep -q 'function switchView' static/js/teacher.js"

# Check load functions exist
test_check "loadDocuments function" \
    "grep -q 'function loadDocuments' static/js/teacher.js || grep -q 'async function loadDocuments' static/js/teacher.js"

test_check "loadDecisionTimeline function" \
    "grep -q 'function loadDecisionTimeline' static/js/teacher.js || grep -q 'async function loadDecisionTimeline' static/js/teacher.js"

test_check "loadQualityReports function" \
    "grep -q 'function loadQualityReports' static/js/teacher.js || grep -q 'async function loadQualityReports' static/js/teacher.js"

# 5. Test Files
echo ""
echo "5. Test Files"
echo "-------------"

test_check "test_s2_2_document_extraction.py exists" \
    "test -f tests/test_s2_2_document_extraction.py"

# Summary
echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}${PASS_COUNT}${NC}"
echo -e "Failed: ${RED}${FAIL_COUNT}${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}Some checks failed. Please review the output above.${NC}"
    exit 1
fi
