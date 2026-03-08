#!/bin/bash
# S2.10 Rollback - 一键回滚到上一稳定 tag；支持 dry-run
# Usage: ./scripts/rollback_s2_10.sh [dry-run]
# 回滚后必须能恢复并通过 health；日志可检索 request_id 与 fallback 轨迹
set -uo pipefail

DRY_RUN="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "S2.10 ROLLBACK $( [ -n "$DRY_RUN" ] && echo "(DRY-RUN)" )"
echo "=============================================="

do_cmd() {
  echo "  $ $*"
  [ -z "$DRY_RUN" ] && "$@"
}

# 1. Stop services
echo ""
echo "1. Stop services"
do_cmd docker compose -f docker-compose.yml down

# 2. Optional: revert to previous stable tag (manual - user must set PREV_TAG or use current)
#    e.g. PREV_TAG=v2.9.0 ./scripts/rollback_s2_10.sh
if [ -n "${PREV_TAG:-}" ]; then
  echo ""
  echo "2. Checkout previous tag: $PREV_TAG"
  do_cmd git checkout "$PREV_TAG"
else
  echo ""
  echo "2. No PREV_TAG set; keeping current code. Set PREV_TAG=v2.x to revert code."
fi

# 3. Rebuild and start
echo ""
echo "3. Rebuild and start"
do_cmd docker compose -f docker-compose.yml up --build -d

# 4. Migration
echo ""
echo "4. Migration (alembic upgrade head)"
do_cmd docker compose exec -T web alembic upgrade head 2>/dev/null || true

# 5. Health check
echo ""
echo "5. Health check (request_id/fallback in logs after LLM calls)"
sleep 5
HEALTH_URL="http://localhost:5001/api/health"
if [ -z "$DRY_RUN" ]; then
  curl -sf "$HEALTH_URL" | head -1 || echo "  (wait for web; then: curl -s $HEALTH_URL)"
else
  echo "  Would verify: curl -s $HEALTH_URL"
fi
echo ""
echo "Rollback complete. Verify: curl -s $HEALTH_URL"
echo "Logs: docker compose logs web | grep -E 'request_id|fallback_triggered|cscl_llm_request'"
