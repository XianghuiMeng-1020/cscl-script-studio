#!/usr/bin/env bash
# 检查 Render 部署状态：health 接口 + 双轨 LLM 配置
# 用法: ./scripts/check_render_deploy.sh [BASE_URL]
# 例:   ./scripts/check_render_deploy.sh https://cscl-script-studio.onrender.com

set -e
BASE_URL="${1:-https://cscl-script-studio.onrender.com}"
API="${BASE_URL}/api"

echo "=== 检查 Render 部署: $BASE_URL ==="
echo ""

# 1. Health 接口
echo "1. GET $API/health"
CODE=$(curl -s -o /tmp/render_health.json -w "%{http_code}" "$API/health" 2>/dev/null || echo "000")
if [ "$CODE" != "200" ]; then
  echo "   状态码: $CODE (期望 200)"
  [ -f /tmp/render_health.json ] && cat /tmp/render_health.json | head -5
  exit 1
fi
echo "   状态码: 200 OK"

# 2. 解析关键字段
if command -v jq &>/dev/null; then
  echo ""
  echo "2. 健康与 LLM 配置:"
  jq -r '
    "   status: \(.status)",
    "   llm_primary: \(.llm_primary)",
    "   llm_fallback: \(.llm_fallback)",
    "   llm_strategy: \(.llm_strategy)",
    "   llm_provider_ready: \(.llm_provider_ready)",
    "   llm_provider_name: \(.llm_provider_name)",
    "   llm_provider_reason: \(.llm_provider_reason)"
  ' /tmp/render_health.json 2>/dev/null || true
  READY=$(jq -r '.llm_provider_ready' /tmp/render_health.json 2>/dev/null)
  if [ "$READY" = "true" ]; then
    echo ""
    echo "   ✅ LLM 已就绪，可正常跑 Pipeline（OpenAI）"
  else
    REASON=$(jq -r '.llm_provider_reason // "unknown"' /tmp/render_health.json 2>/dev/null)
    echo ""
    echo "   ⚠️  LLM 未就绪: $REASON"
    echo "   请确认 Render Environment 中已设置 OPENAI_API_KEY"
  fi
else
  echo ""
  echo "2. 原始响应 (无 jq 时):"
  grep -E '"status"|"llm_primary"|"llm_fallback"|"llm_provider_ready"|"llm_provider_reason"' /tmp/render_health.json 2>/dev/null || cat /tmp/render_health.json
fi
echo ""
echo "完成。若 llm_provider_ready 为 true，说明部署正常。"
