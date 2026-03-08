#!/bin/bash
# S2.18 Acceptance Test Script

set -e

BASE_URL="${BASE_URL:-http://localhost:5001}"
echo "=== S2.18 Acceptance Tests ==="
echo ""

# Test 1: Health endpoint exposes provider readiness fields
echo "Test 1: Health endpoint exposes provider readiness fields"
HEALTH=$(curl -sS "${BASE_URL}/api/health" 2>/dev/null || echo "{}")
if echo "$HEALTH" | python3 -c "import sys, json; d=json.load(sys.stdin); assert 'llm_provider_ready' in d and 'llm_provider_name' in d and 'llm_provider_reason' in d, 'Missing fields'; print('✓ PASS: Health endpoint includes llm_provider_ready, llm_provider_name, llm_provider_reason')" 2>/dev/null; then
    echo "$HEALTH" | python3 -m json.tool | grep -E "(llm_provider_ready|llm_provider_name|llm_provider_reason)" || true
else
    echo "✗ FAIL: Health endpoint missing required fields"
    exit 1
fi
echo ""

# Test 2: Provider selection never picks unimplemented OpenAI
echo "Test 2: Provider selection logic (requires Python test)"
echo "  Run: python3 -m pytest tests/test_s2_18_provider_selection.py::test_select_runnable_provider_never_picks_unimplemented_openai -v"
echo ""

# Test 3: Pipeline returns 503 when provider not ready
echo "Test 3: Pipeline returns 503 LLM_PROVIDER_NOT_READY"
echo "  Run: python3 -m pytest tests/test_s2_18_provider_selection.py::test_pipeline_returns_503_when_openai_not_implemented -v"
echo ""

# Test 4: No pending stages when provider not ready
echo "Test 4: No pending stages created"
echo "  Run: python3 -m pytest tests/test_s2_18_provider_selection.py::test_pipeline_no_pending_stage_when_provider_not_ready -v"
echo ""

# Test 5: Verify default is qwen, not openai
echo "Test 5: Verify default provider is qwen"
if grep -q "LLM_PROVIDER_PRIMARY.*qwen" app/config.py && grep -q "LLM_PROVIDER_PRIMARY.*qwen" docker-compose.yml && grep -q "LLM_PROVIDER_PRIMARY=qwen" .env.example; then
    echo "✓ PASS: Default LLM_PROVIDER_PRIMARY is qwen in config.py, docker-compose.yml, .env.example"
else
    echo "✗ FAIL: Default LLM_PROVIDER_PRIMARY is not qwen everywhere"
    exit 1
fi
echo ""

echo "=== Manual Verification Required ==="
echo ""
echo "1. Run pytest tests:"
echo "   python3 -m pytest tests/test_s2_18_provider_selection.py -v"
echo ""
echo "2. Check health endpoint:"
echo "   curl -s ${BASE_URL}/api/health | jq '{llm_provider_ready, llm_provider_name, llm_provider_reason}'"
echo ""
echo "3. Test pipeline with unimplemented OpenAI:"
echo "   export LLM_PROVIDER_PRIMARY=openai"
echo "   export OPENAI_ENABLED=true"
echo "   export OPENAI_IMPLEMENTED=false"
echo "   export LLM_ALLOW_UNIMPLEMENTED_PRIMARY=false"
echo "   export QWEN_API_KEY=test-key"
echo "   # Then run pipeline - should use qwen or return 503"
echo ""
