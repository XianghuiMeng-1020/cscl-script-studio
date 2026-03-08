#!/bin/bash
# API联调测试脚本

BASE_URL="${BASE_URL:-http://localhost:5001}"
API_BASE="${BASE_URL}/api"
CSCL_BASE="${API_BASE}/cscl"

echo "=== CSCL Frontend API Integration Tests ==="
echo "Base URL: ${BASE_URL}"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

test_api() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    local expected_status=$5
    
    echo -n "Testing ${name}... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "${url}")
    else
        response=$(curl -s -w "\n%{http_code}" -X "${method}" \
            -H "Content-Type: application/json" \
            -d "${data}" \
            "${url}")
    fi
    
    http_code=$(echo "${response}" | tail -n1)
    body=$(echo "${response}" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ] || [ -z "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} (${http_code})"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} (Expected ${expected_status}, got ${http_code})"
        echo "  Response: ${body}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# 1. Health Check
test_api "Health Check" "GET" "${API_BASE}/health" "" "200"

# 2. Demo Init
test_api "Demo Init" "POST" "${API_BASE}/demo/init" "" "200"

# 3. Spec Validation (public endpoint)
SPEC='{
  "course": "CS101",
  "topic": "Algorithmic Fairness",
  "duration_minutes": 90,
  "mode": "Sync",
  "class_size": 30,
  "learning_objectives": ["Objective 1"],
  "task_type": "debate"
}'
test_api "Spec Validation" "POST" "${CSCL_BASE}/spec/validate" "${SPEC}" "200"

# 4. Check pages return 200
echo ""
echo "=== Page Availability Tests ==="
for page in "/" "/teacher" "/student"; do
    echo -n "Testing ${page}... "
    status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}${page}")
    if [ "$status" = "200" ]; then
        echo -e "${GREEN}✓${NC} (${status})"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} (${status})"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=== Test Summary ==="
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo "Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed.${NC}"
    exit 1
fi
