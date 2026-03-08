#!/bin/bash
# S2.13 PDF_TEXT_PIPELINE_HARDFIX gate: no binary in preview; pytest s2_13 + full suite.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
ENV_FILE="${ENV_FILE:-.env}"
if [ ! -f "$ENV_FILE" ]; then
    ENV_FILE=".env.example"
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'
FAILED_ITEM=""

run_step() {
    local name="$1"
    shift
    echo ""
    echo "--- $name ---"
    if "$@" 2>&1; then
        echo -e "${GREEN}PASS: $name${NC}"
        return 0
    else
        echo -e "${RED}FAIL: $name${NC}"
        FAILED_ITEM="$name"
        return 1
    fi
}

echo "=============================================="
echo "S2.13 PDF_TEXT_PIPELINE_HARDFIX GATE"
echo "=============================================="

run_step "1. docker compose down -v" docker compose --env-file "$ENV_FILE" down -v || true
run_step "2. docker compose up --build -d" docker compose --env-file "$ENV_FILE" up --build -d
sleep 15
run_step "3. alembic upgrade head" docker compose --env-file "$ENV_FILE" exec -T web alembic upgrade head
run_step "4. seed_demo_users" docker compose --env-file "$ENV_FILE" exec -T web python scripts/seed_demo_users.py
run_step "5. pytest test_s2_13_pdf_binary_guard" docker compose --env-file "$ENV_FILE" exec -T web python -m pytest tests/test_s2_13_pdf_binary_guard.py -q --tb=short
run_step "6. pytest tests/ full" docker compose --env-file "$ENV_FILE" exec -T web python -m pytest tests/ -q --tb=short

echo ""
echo "=============================================="
if [ -n "$FAILED_ITEM" ]; then
    echo -e "${RED}FAILED: $FAILED_ITEM${NC}"
    echo "=============================================="
    exit 1
fi
echo -e "${GREEN}ALL STEPS PASSED${NC}"
echo "=============================================="
exit 0
