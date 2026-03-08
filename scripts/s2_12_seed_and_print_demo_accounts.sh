#!/bin/bash
# S2.12: Run seed_demo_users.py and print demo account list (dev/demo only).
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Prefer running inside container if available
if command -v docker >/dev/null 2>&1 && docker compose exec -T web true 2>/dev/null; then
    docker compose exec -T web python scripts/seed_demo_users.py
else
    python scripts/seed_demo_users.py
fi

echo ""
echo "=============================================="
echo "Demo accounts (for login):"
echo "  teacher_demo / Demo@12345  -> /teacher"
echo "  student_demo / Demo@12345  -> /student"
echo "  admin_demo   / Demo@12345  -> /teacher (admin)"
echo "=============================================="
