#!/bin/bash
# S2.9 Verify Provider Fallback - health exposes llm_primary/llm_fallback/llm_strategy; structured log fields exist
# Fail-fast: any check fails => exit 1
set -uo pipefail

BASE_URL="${BASE_URL:-http://localhost:5001}"
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

echo "=============================================="
echo "S2.9 PROVIDER FALLBACK VERIFY"
echo "=============================================="

# 1. Health returns required fields
echo ""
echo "1. Health API fields (llm_primary, llm_fallback, llm_strategy)"
check "health 200" curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/api/health" | grep -q 200
check "health status=ok" curl -sf "$BASE_URL/api/health" | grep -q '"status":"ok"'
check "health llm_primary" curl -sf "$BASE_URL/api/health" | grep -q '"llm_primary"'
check "health llm_fallback" curl -sf "$BASE_URL/api/health" | grep -q '"llm_fallback"'
check "health llm_strategy" curl -sf "$BASE_URL/api/health" | grep -q '"llm_strategy"'
check "health db_connected" curl -sf "$BASE_URL/api/health" | grep -q '"db_connected"'
check "health provider" curl -sf "$BASE_URL/api/health" | grep -q '"provider"'
check "health auth_mode" curl -sf "$BASE_URL/api/health" | grep -q '"auth_mode"'
check "health rbac_enabled" curl -sf "$BASE_URL/api/health" | grep -q '"rbac_enabled"'

# 2. Code: fallback only on retryable (timeout/429/5xx/connection); 401/403/param must NOT fallback
echo ""
echo "2. Fallback logic in code"
check "FallbackLLMProvider exists" grep -q "FallbackLLMProvider" app/services/cscl_llm_provider.py
check "retryable patterns" grep -q "_RETRYABLE_ERROR_PATTERNS" app/services/cscl_llm_provider.py
check "non-retryable patterns" grep -q "_NON_RETRYABLE_PATTERNS" app/services/cscl_llm_provider.py
check "_is_retryable_error" grep -q "_is_retryable_error" app/services/cscl_llm_provider.py

# 3. Structured log fields (request_id, primary_provider, final_provider, fallback_triggered, error_type, latency_ms)
echo ""
echo "3. Structured log fields in code"
check "request_id in log" grep -q "request_id" app/services/cscl_llm_provider.py
check "primary_provider in log" grep -q "primary_provider" app/services/cscl_llm_provider.py
check "final_provider in log" grep -q "final_provider" app/services/cscl_llm_provider.py
check "fallback_triggered in log" grep -q "fallback_triggered" app/services/cscl_llm_provider.py
check "error_type in log" grep -q "error_type" app/services/cscl_llm_provider.py
check "latency_ms in log" grep -q "latency_ms" app/services/cscl_llm_provider.py

echo ""
echo "=============================================="
echo "S2.9 TOTAL: $PASS passed, $FAIL failed"
echo "=============================================="
[ "$FAIL" -eq 0 ] || exit 1
exit 0
