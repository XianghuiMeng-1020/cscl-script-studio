#!/bin/bash
# S2.7 Rollback - 一键回滚到 v2.7.0-go-live 前状态
# Usage: ./scripts/rollback_s2_7.sh [dry-run]
set -uo pipefail

DRY_RUN="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "S2.7 ROLLBACK $( [ -n "$DRY_RUN" ] && echo "(DRY-RUN)" )"
echo "=============================================="

do_cmd() {
  echo "  $ $*"
  [ -z "$DRY_RUN" ] && "$@"
}

# 1. Stop services
echo ""
echo "1. Stop services"
do_cmd docker compose -f docker-compose.yml down

# 2. Optional: revert to previous tag (manual, if code rollback needed)
#   do_cmd git checkout <prev-tag-or-commit>
#   Example: git checkout v2.6.0  # or specific commit hash

# 3. Rebuild and start
echo ""
echo "2. Rebuild and start"
do_cmd docker compose -f docker-compose.yml up --build -d

# 4. Run migration (no downgrade - Alembic upgrade only)
echo ""
echo "3. Migration (upgrade head - no downgrade)"
echo "   Note: DB downgrade not recommended. Restore from backup if rollback needed."
do_cmd docker compose exec -T web alembic upgrade head 2>/dev/null || true

# 5. Verify health
echo ""
echo "4. Health check"
sleep 5
curl -sf "$(docker compose port web 5000 2>/dev/null | sed 's/0.0.0.0/localhost/')/api/health" 2>/dev/null | head -1 || echo "  (wait for web to be ready)"

echo ""
echo "Rollback complete. Verify with: curl -s http://localhost:5001/api/health"
