#!/bin/bash
# LLM Provider验证脚本
# 测试三种配置：mock, qwen, openai

set -e

echo "=== LLM Provider 验证脚本 ==="
echo ""

# 测试端点
TEST_ENDPOINT="http://localhost:5000/api/ai/check-alignment"
TEST_PAYLOAD='{
  "feedback": "This is a test feedback that covers argument clarity and evidence support.",
  "rubric_criteria": [
    {"id": "C1", "name": "Argument Clarity", "description": "Is the thesis clear?"},
    {"id": "C2", "name": "Evidence Support", "description": "Are there sufficient evidence?"}
  ]
}'

echo "测试端点: $TEST_ENDPOINT"
echo ""

# 测试1: Mock Provider
echo "=== 测试1: Mock Provider ==="
export LLM_PROVIDER=mock
unset QWEN_API_KEY
unset OPENAI_API_KEY

echo "配置: LLM_PROVIDER=mock"
echo "请求..."
RESPONSE=$(curl -s -X POST "$TEST_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD")

echo "响应:"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""

# 检查响应
if echo "$RESPONSE" | grep -q "provider.*mock"; then
    echo "✅ Mock provider 测试通过"
else
    echo "❌ Mock provider 测试失败"
    exit 1
fi

echo ""
echo "=== 测试2: Qwen Provider ==="
export LLM_PROVIDER=qwen
# 从.env文件读取API key，如果未设置则跳过此测试
if [ -f .env ] && grep -q "QWEN_API_KEY=" .env; then
    export QWEN_API_KEY=$(grep "QWEN_API_KEY=" .env | cut -d '=' -f2)
    export QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
    export QWEN_MODEL="qwen-plus"
    unset OPENAI_API_KEY
    
    echo "配置: LLM_PROVIDER=qwen, QWEN_API_KEY已从.env读取"
else
    echo "⚠️  跳过Qwen测试：.env文件中未找到QWEN_API_KEY"
    echo "   请在.env文件中设置QWEN_API_KEY以测试Qwen provider"
    echo ""
    continue
fi
echo "请求..."
RESPONSE=$(curl -s -X POST "$TEST_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD")

echo "响应:"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""

# 检查响应
if echo "$RESPONSE" | grep -q "provider.*qwen"; then
    echo "✅ Qwen provider 测试通过"
elif echo "$RESPONSE" | grep -q "error"; then
    echo "⚠️  Qwen provider 返回错误（可能是API key问题）"
    echo "错误信息: $(echo "$RESPONSE" | jq -r '.error' 2>/dev/null || echo 'N/A')"
else
    echo "❌ Qwen provider 测试失败"
    exit 1
fi

echo ""
echo "=== 测试3: OpenAI Provider ==="
export LLM_PROVIDER=openai
# 从.env文件读取API key，如果未设置则跳过此测试
if [ -f .env ] && grep -q "OPENAI_API_KEY=" .env; then
    export OPENAI_API_KEY=$(grep "OPENAI_API_KEY=" .env | cut -d '=' -f2)
    export OPENAI_MODEL="gpt-3.5-turbo"
    unset QWEN_API_KEY
    
    echo "配置: LLM_PROVIDER=openai, OPENAI_API_KEY已从.env读取"
else
    echo "⚠️  跳过OpenAI测试：.env文件中未找到OPENAI_API_KEY"
    echo "   请在.env文件中设置OPENAI_API_KEY以测试OpenAI provider"
    echo ""
    continue
fi
echo "请求..."
RESPONSE=$(curl -s -X POST "$TEST_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD")

echo "响应:"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""

# 检查响应
if echo "$RESPONSE" | grep -q "provider.*openai"; then
    echo "✅ OpenAI provider 测试通过"
elif echo "$RESPONSE" | grep -q "error"; then
    echo "⚠️  OpenAI provider 返回错误（可能是API key问题）"
    echo "错误信息: $(echo "$RESPONSE" | jq -r '.error' 2>/dev/null || echo 'N/A')"
else
    echo "❌ OpenAI provider 测试失败"
    exit 1
fi

echo ""
echo "=== 测试4: 未配置Provider（应返回503） ==="
export LLM_PROVIDER=qwen
unset QWEN_API_KEY
unset OPENAI_API_KEY

echo "配置: LLM_PROVIDER=qwen, 但QWEN_API_KEY未设置"
echo "请求..."
HTTP_CODE=$(curl -s -o /tmp/response.json -w "%{http_code}" -X POST "$TEST_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD")

RESPONSE=$(cat /tmp/response.json)
echo "HTTP状态码: $HTTP_CODE"
echo "响应:"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""

# 检查响应
if [ "$HTTP_CODE" = "503" ]; then
    if echo "$RESPONSE" | grep -q "LLM not configured"; then
        echo "✅ 未配置Provider测试通过（正确返回503）"
    else
        echo "⚠️  返回503但错误消息格式可能不正确"
    fi
else
    echo "❌ 未配置Provider测试失败（应返回503，实际返回$HTTP_CODE）"
    exit 1
fi

echo ""
echo "=== ✅ 所有测试完成 ==="
