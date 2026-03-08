#!/bin/bash
# LLM Provider三种模式完整测试脚本

ENDPOINT="http://localhost:5000/api/ai/check-alignment"
PAYLOAD='{
  "feedback": "This feedback covers argument clarity and evidence support.",
  "rubric_criteria": [
    {"id": "C1", "name": "Argument Clarity", "description": "Is the thesis clear?"},
    {"id": "C2", "name": "Evidence Support", "description": "Are there sufficient evidence?"}
  ]
}'

echo "============================================================"
echo "LLM Provider三种模式验收测试"
echo "============================================================"
echo ""
echo "⚠️  注意: 每次切换provider后需要重启Flask应用"
echo "   修改.env文件中的LLM_PROVIDER，然后重启服务"
echo ""

# 检查服务器是否运行
if ! curl -s http://localhost:5000/ > /dev/null 2>&1; then
    echo "❌ Flask服务器未运行"
    echo "   请先启动: python3 app.py 或 docker compose up"
    exit 1
fi

echo "✅ Flask服务器正在运行"
echo ""

# 读取当前配置
if [ -f .env ]; then
    CURRENT_PROVIDER=$(grep "^LLM_PROVIDER=" .env | cut -d '=' -f2)
    echo "当前配置的Provider: ${CURRENT_PROVIDER:-未设置}"
    echo ""
fi

echo "============================================================"
echo "测试1: Mock Provider"
echo "============================================================"
echo "配置要求: LLM_PROVIDER=mock (不需要API key)"
echo ""
echo "Curl命令:"
echo "curl -X POST $ENDPOINT \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '$PAYLOAD'"
echo ""
echo "执行测试..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d ':' -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo "HTTP状态码: $HTTP_CODE"
echo "响应内容:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    if echo "$BODY" | grep -q '"provider".*"mock"'; then
        echo "✅ Mock Provider测试通过"
    else
        echo "⚠️  返回200但provider不是mock，请检查配置"
    fi
elif [ "$HTTP_CODE" = "503" ]; then
    echo "⚠️  返回503，可能是provider配置错误或API key问题"
else
    echo "❌ 意外的HTTP状态码: $HTTP_CODE"
fi

echo ""
echo "============================================================"
echo "测试2: Qwen Provider"
echo "============================================================"
echo "配置要求: LLM_PROVIDER=qwen, QWEN_API_KEY已设置"
echo ""
echo "Curl命令:"
echo "curl -X POST $ENDPOINT \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '$PAYLOAD'"
echo ""
echo "执行测试..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d ':' -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo "HTTP状态码: $HTTP_CODE"
echo "响应内容:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    if echo "$BODY" | grep -q '"provider".*"qwen"'; then
        echo "✅ Qwen Provider测试通过（API调用成功）"
    else
        echo "⚠️  返回200但provider不是qwen"
    fi
elif [ "$HTTP_CODE" = "503" ]; then
    if echo "$BODY" | grep -q "QWEN_API_KEY not configured"; then
        echo "✅ Qwen Provider未配置测试通过（正确返回503）"
    else
        echo "⚠️  返回503但错误信息可能不正确"
    fi
else
    echo "❌ 意外的HTTP状态码: $HTTP_CODE"
fi

echo ""
echo "============================================================"
echo "测试3: OpenAI Provider"
echo "============================================================"
echo "配置要求: LLM_PROVIDER=openai, OPENAI_API_KEY已设置"
echo ""
echo "Curl命令:"
echo "curl -X POST $ENDPOINT \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '$PAYLOAD'"
echo ""
echo "执行测试..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d ':' -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo "HTTP状态码: $HTTP_CODE"
echo "响应内容:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    if echo "$BODY" | grep -q '"provider".*"openai"'; then
        echo "✅ OpenAI Provider测试通过（API调用成功）"
    else
        echo "⚠️  返回200但provider不是openai"
    fi
elif [ "$HTTP_CODE" = "503" ]; then
    if echo "$BODY" | grep -q "OPENAI_API_KEY not configured"; then
        echo "✅ OpenAI Provider未配置测试通过（正确返回503）"
    else
        echo "⚠️  返回503但错误信息可能不正确"
    fi
else
    echo "❌ 意外的HTTP状态码: $HTTP_CODE"
fi

echo ""
echo "============================================================"
echo "测试完成"
echo "============================================================"
echo ""
echo "提示: 要切换provider，修改.env文件中的LLM_PROVIDER，然后重启Flask应用"
