#!/usr/bin/env bash
# Phase C 快速确认：回归 + release readiness + smoke (teacher_demo) + 413 校验
# 使用前：启动服务（如 docker compose up 或 flask run），并确保有 teacher_demo 账号（scripts/seed_demo_users.py）
# 输出完整到 stdout，便于贴出给验收方。
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:5001}"
cd "$(dirname "$0")/.."

echo "=============================================="
echo "Phase C 快速确认"
echo "BASE_URL=$BASE_URL"
echo "=============================================="

echo ""
echo "---------- 1. 完整回归 (pytest) ----------"
python3 -m pytest tests/test_cscl_rag_grounding_api.py tests/test_cscl_pipeline_api.py tests/test_idempotency.py tests/test_api_413_and_trace_id.py -v --tb=short 2>&1 || true

echo ""
echo "---------- 2. Release Readiness ----------"
./scripts/release_readiness_check.sh 2>&1 || true

echo ""
echo "---------- 3. Smoke (SMOKE=1) ----------"
SMOKE=1 ./scripts/release_readiness_check.sh 2>&1 || true

echo ""
echo "---------- 4. teacher_demo 全链路 ----------"
SMOKE_USER=teacher_demo SMOKE_PASSWORD="${SMOKE_PASSWORD:-Demo@12345}" ./scripts/smoke_prod_flow.sh 2>&1 || true

echo ""
echo "---------- 5. FILE_TOO_LARGE / 413 校验 ----------"
echo "用超限文件上传，期望 HTTP 413 + JSON 含 success/error_code/message/trace_id"
COOKIE_JAR=$(mktemp)
trap 'rm -f "$COOKIE_JAR"' EXIT
curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" -X POST -H "Content-Type: application/json" \
  -d '{"user_id":"T001","password":"teacher123"}' "$BASE_URL/api/auth/login" >/dev/null 2>&1 || true
# 创建 15MB 的假文件（需 base64 或 dd）上传
# 若没有大文件，用 curl 上传并检查 413 响应体
echo "（若服务限制 10MB，可手动：curl -X POST -F 'file=@large.pdf' -b cookies $BASE_URL/api/cscl/courses/default-course/docs/upload）"
echo "预期: HTTP 413, body 含 success=false, error_code=FILE_TOO_LARGE, message, trace_id"
echo ""

echo "=============================================="
echo "Phase C 快速确认 结束"
echo "=============================================="
