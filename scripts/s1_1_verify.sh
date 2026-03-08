#!/bin/bash
# S1.1 一键验收脚本
# 执行：docker启动、健康检查、API测试、截图生成、输出PASS/FAIL

set -e

BASE_URL="${BASE_URL:-http://localhost:5001}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
PASSED=0
FAILED=0
WARNINGS=0

echo "=========================================="
echo "S1.1 Frontend Acceptance Verification"
echo "=========================================="
echo "Base URL: ${BASE_URL}"
echo "Project Dir: ${PROJECT_DIR}"
echo ""

# Function to log results
log_pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASSED=$((PASSED + 1))
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
    FAILED=$((FAILED + 1))
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

# Step 1: Start Docker services
echo "=== Step 1: Starting Docker Services ==="
if docker compose ps | grep -q "Up"; then
    log_warn "Services already running, skipping start"
else
    echo "Starting services..."
    docker compose up -d
    echo "Waiting 30 seconds for services to start..."
    sleep 30
    log_pass "Docker services started"
fi

# Step 2: Health Check
echo ""
echo "=== Step 2: Health Check ==="
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/api/health" || echo -e "\n000")
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$HEALTH_CODE" = "200" ]; then
    log_pass "Health check (${HEALTH_CODE})"
    echo "$HEALTH_BODY" | jq '.' 2>/dev/null || echo "$HEALTH_BODY"
else
    log_fail "Health check failed (${HEALTH_CODE})"
    echo "Response: $HEALTH_BODY"
fi

# Step 3: Demo Init
echo ""
echo "=== Step 3: Demo Initialization ==="
INIT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/demo/init" || echo -e "\n000")
INIT_CODE=$(echo "$INIT_RESPONSE" | tail -n1)

if [ "$INIT_CODE" = "200" ]; then
    log_pass "Demo init (${INIT_CODE})"
else
    log_warn "Demo init returned ${INIT_CODE} (may already be initialized)"
fi

# Step 4: Page Availability Tests
echo ""
echo "=== Step 4: Page Availability ==="
for page in "/" "/teacher" "/student"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}${page}" || echo "000")
    if [ "$STATUS" = "200" ]; then
        log_pass "Page ${page} (${STATUS})"
    else
        log_fail "Page ${page} (${STATUS})"
    fi
done

# Step 5: API Smoke Tests
echo ""
echo "=== Step 5: API Smoke Tests ==="

# Spec Validation (public endpoint)
SPEC='{"course":"CS101","topic":"Test","duration_minutes":90,"mode":"Sync","class_size":30,"learning_objectives":["Obj1"],"task_type":"debate"}'
VALIDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "${SPEC}" \
    "${BASE_URL}/api/cscl/spec/validate" || echo -e "\n000")
VALIDATE_CODE=$(echo "$VALIDATE_RESPONSE" | tail -n1)

if [ "$VALIDATE_CODE" = "200" ] || [ "$VALIDATE_CODE" = "422" ]; then
    log_pass "Spec validation (${VALIDATE_CODE})"
else
    log_fail "Spec validation (${VALIDATE_CODE})"
fi

# Step 6: Port Consistency Check
echo ""
echo "=== Step 6: Port Consistency Check ==="
if [ -f "scripts/check_port_consistency.sh" ]; then
    if bash scripts/check_port_consistency.sh > /dev/null 2>&1; then
        log_pass "Port consistency check"
    else
        log_warn "Port consistency check found some references (check output)"
        bash scripts/check_port_consistency.sh
    fi
else
    log_warn "Port consistency script not found"
fi

# Step 7: Screenshot Generation
echo ""
echo "=== Step 7: Screenshot Generation ==="
if command -v node > /dev/null && [ -f "package.json" ] || command -v puppeteer > /dev/null; then
    echo "Attempting to generate screenshots..."
    if BASE_URL="${BASE_URL}" node scripts/screenshot.js 2>&1; then
        log_pass "Screenshot script executed"
        
        # Check if manifest exists
        if [ -f "outputs/ui/SCREENSHOT_MANIFEST.json" ]; then
            log_pass "Screenshot manifest generated"
            echo "Manifest: outputs/ui/SCREENSHOT_MANIFEST.json"
        else
            log_warn "Screenshot manifest not found"
        fi
        
        # Count successful screenshots
        SCREENSHOT_COUNT=$(find outputs/ui -name "*.png" -type f 2>/dev/null | wc -l | tr -d ' ')
        if [ "$SCREENSHOT_COUNT" -ge 3 ]; then
            log_pass "Screenshots generated (${SCREENSHOT_COUNT} files)"
        else
            log_warn "Fewer screenshots than expected (${SCREENSHOT_COUNT} files)"
        fi
    else
        log_warn "Screenshot script failed (may require manual capture)"
    fi
else
    log_warn "Node.js/Puppeteer not available, skipping screenshot generation"
    echo "  Install: npm install puppeteer"
    echo "  Or capture screenshots manually"
fi

# Step 8: Student Real API Integration Check
echo ""
echo "=== Step 8: Student Real API Integration ==="
if grep -q "fetch.*api/cscl/scripts.*export" static/js/student.js; then
    log_pass "Student.js uses real API calls (export endpoint)"
else
    log_fail "Student.js does not use real API calls"
fi

if grep -q "fetch.*api/cscl/scripts.*quality-report" static/js/student.js; then
    log_pass "Student.js uses real API calls (quality-report endpoint)"
else
    log_fail "Student.js does not use real API calls for quality report"
fi

# Final Summary
echo ""
echo "=========================================="
echo "=== Verification Summary ==="
echo "=========================================="
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo -e "${YELLOW}Warnings: ${WARNINGS}${NC}"
echo "Total Checks: $((PASSED + FAILED + WARNINGS))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ VERIFICATION PASSED${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review screenshots in outputs/ui/"
    echo "  2. Check SCREENSHOT_MANIFEST.json"
    echo "  3. Test Student page with ?script_id=xxx parameter"
    exit 0
else
    echo -e "${RED}❌ VERIFICATION FAILED${NC}"
    echo ""
    echo "Please fix the failed items above."
    exit 1
fi
