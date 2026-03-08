#!/bin/bash
# ===== S2.13 ENV FIX + GO-LIVE SMOKE =====
# 在具备 Docker 与外网的环境执行（需能访问 deb.debian.org 等）
set -e
cd "$(dirname "$0")/.."

echo "[1/8] Stop stack"
docker compose --env-file .env down -v || true

echo "[2/8] Docker builder cleanup"
docker builder prune -af || true
docker image prune -af || true
docker volume prune -f || true

echo "[3/8] Desktop VM disk cleanup hint done"

echo "[4/8] Rebuild without cache"
DOCKER_BUILDKIT=1 docker compose --env-file .env build --no-cache web

echo "[5/8] Start services"
docker compose --env-file .env up -d

echo "[6/8] Migrate + seed"
sleep 15
docker compose --env-file .env exec web alembic upgrade head
docker compose --env-file .env exec web python scripts/seed_demo_users.py

echo "[7/8] Verify health + auth pages"
curl -s http://localhost:5001/api/health
curl -I http://localhost:5001/login | head -n 1
curl -I http://localhost:5001/demo  | head -n 1
curl -I http://localhost:5001/teacher | head -n 1
curl -I http://localhost:5001/student | head -n 1

echo "[8/8] Run gates"
docker compose --env-file .env exec web python -m pytest tests/ -q
./scripts/s2_5_release_gate.sh
bash ./scripts/s2_13_pdf_gate.sh || true

echo "DONE"
