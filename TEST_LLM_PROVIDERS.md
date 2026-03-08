# LLM Provider三种模式验收测试

## 测试前提

1. 确保Flask应用正在运行：
   ```bash
   # 方法1: 直接运行
   python3 app.py
   
   # 方法2: Docker
   docker compose up
   ```

2. 确保`.env`文件已配置（包含真实API key）

3. 测试端点: `POST http://localhost:5000/api/ai/check-alignment`

---

## 测试数据

```json
{
  "feedback": "This feedback covers argument clarity and evidence support.",
  "rubric_criteria": [
    {"id": "C1", "name": "Argument Clarity", "description": "Is the thesis clear?"},
    {"id": "C2", "name": "Evidence Support", "description": "Are there sufficient evidence?"}
  ]
}
```

---

## 测试A: Mock Provider

### 配置步骤

```bash
# 1. 设置环境变量（或修改.env文件）
export LLM_PROVIDER=mock
unset QWEN_API_KEY
unset OPENAI_API_KEY

# 2. 重启Flask应用以加载新环境变量
# 停止当前进程，然后重新运行: python3 app.py
```

### Curl命令

```bash
curl -X POST http://localhost:5000/api/ai/check-alignment \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "This feedback covers argument clarity and evidence support.",
    "rubric_criteria": [
      {"id": "C1", "name": "Argument Clarity", "description": "Is the thesis clear?"},
      {"id": "C2", "name": "Evidence Support", "description": "Are there sufficient evidence?"}
    ]
  }'
```

### 预期输出

**HTTP状态码**: `200`

**响应JSON**:
```json
{
  "provider": "mock",
  "model": "mock-model-v1",
  "covered_criteria": [
    "Argument Clarity",
    "Evidence Support"
  ],
  "missing_criteria": [
    "Organization",
    "Language Expression"
  ],
  "coverage_score": 50,
  "suggestions": [
    "Consider adding feedback on organization",
    "Mention language expression"
  ],
  "warnings": [
    "This is a mock provider response for testing"
  ]
}
```

**验证点**:
- ✅ HTTP状态码为200
- ✅ `provider`字段为`"mock"`
- ✅ `model`字段为`"mock-model-v1"`
- ✅ 包含`covered_criteria`和`missing_criteria`数组
- ✅ `coverage_score`为数字
- ✅ `warnings`数组包含mock提示信息

---

## 测试B: Qwen Provider

### 配置步骤

```bash
# 1. 设置环境变量（或修改.env文件）
export LLM_PROVIDER=qwen
export QWEN_API_KEY="sk-2cedfc30d0af4fef84acf12451d0bf32"
export QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export QWEN_MODEL="qwen-plus"
unset OPENAI_API_KEY

# 2. 重启Flask应用
```

### Curl命令

```bash
curl -X POST http://localhost:5000/api/ai/check-alignment \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "This feedback covers argument clarity and evidence support.",
    "rubric_criteria": [
      {"id": "C1", "name": "Argument Clarity", "description": "Is the thesis clear?"},
      {"id": "C2", "name": "Evidence Support", "description": "Are there sufficient evidence?"}
    ]
  }'
```

### 预期输出（成功时）

**HTTP状态码**: `200`

**响应JSON**:
```json
{
  "provider": "qwen",
  "model": "qwen-plus",
  "covered_criteria": [
    "Argument Clarity",
    "Evidence Support"
  ],
  "missing_criteria": [],
  "coverage_score": 100,
  "suggestions": []
}
```

**验证点**:
- ✅ HTTP状态码为200
- ✅ `provider`字段为`"qwen"`
- ✅ `model`字段为`"qwen-plus"`
- ✅ 包含有效的分析结果（covered_criteria, missing_criteria等）

### 预期输出（API key未配置时）

**HTTP状态码**: `503`

**响应JSON**:
```json
{
  "error": "QWEN_API_KEY not configured",
  "provider": "qwen",
  "message": "LLM not configured"
}
```

**验证点**:
- ✅ HTTP状态码为503
- ✅ `error`字段包含明确的错误信息
- ✅ `provider`字段为`"qwen"`

---

## 测试C: OpenAI Provider

### 配置步骤

```bash
# 1. 设置环境变量（或修改.env文件）
export LLM_PROVIDER=openai
export OPENAI_API_KEY="sk-proj-YOUR_OPENAI_KEY_HERE"
export OPENAI_MODEL="gpt-3.5-turbo"
unset QWEN_API_KEY

# 2. 重启Flask应用
```

### Curl命令

```bash
curl -X POST http://localhost:5000/api/ai/check-alignment \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "This feedback covers argument clarity and evidence support.",
    "rubric_criteria": [
      {"id": "C1", "name": "Argument Clarity", "description": "Is the thesis clear?"},
      {"id": "C2", "name": "Evidence Support", "description": "Are there sufficient evidence?"}
    ]
  }'
```

### 预期输出（成功时）

**HTTP状态码**: `200`

**响应JSON**:
```json
{
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "covered_criteria": [
    "Argument Clarity",
    "Evidence Support"
  ],
  "missing_criteria": [],
  "coverage_score": 100,
  "suggestions": []
}
```

**验证点**:
- ✅ HTTP状态码为200
- ✅ `provider`字段为`"openai"`
- ✅ `model`字段为`"gpt-3.5-turbo"`
- ✅ 包含有效的分析结果

### 预期输出（API key未配置时）

**HTTP状态码**: `503`

**响应JSON**:
```json
{
  "error": "OPENAI_API_KEY not configured",
  "provider": "openai",
  "message": "LLM not configured"
}
```

**验证点**:
- ✅ HTTP状态码为503
- ✅ `error`字段包含明确的错误信息
- ✅ `provider`字段为`"openai"`

---

## 快速测试脚本

创建测试脚本 `test_all_providers.sh`:

```bash
#!/bin/bash

ENDPOINT="http://localhost:5000/api/ai/check-alignment"
PAYLOAD='{
  "feedback": "This feedback covers argument clarity and evidence support.",
  "rubric_criteria": [
    {"id": "C1", "name": "Argument Clarity", "description": "Is the thesis clear?"},
    {"id": "C2", "name": "Evidence Support", "description": "Are there sufficient evidence?"}
  ]
}'

echo "=== 测试Mock Provider ==="
export LLM_PROVIDER=mock
unset QWEN_API_KEY OPENAI_API_KEY
# 重启服务后运行
curl -X POST "$ENDPOINT" -H "Content-Type: application/json" -d "$PAYLOAD" | jq '.'

echo -e "\n=== 测试Qwen Provider ==="
export LLM_PROVIDER=qwen
export QWEN_API_KEY="sk-2cedfc30d0af4fef84acf12451d0bf32"
unset OPENAI_API_KEY
# 重启服务后运行
curl -X POST "$ENDPOINT" -H "Content-Type: application/json" -d "$PAYLOAD" | jq '.'

echo -e "\n=== 测试OpenAI Provider ==="
export LLM_PROVIDER=openai
export OPENAI_API_KEY="sk-proj-YOUR_OPENAI_KEY_HERE"
unset QWEN_API_KEY
# 重启服务后运行
curl -X POST "$ENDPOINT" -H "Content-Type: application/json" -d "$PAYLOAD" | jq '.'
```

---

## 验收标准

✅ **所有三种模式都必须通过以下验证**:

1. **Mock Provider**:
   - HTTP 200
   - 返回mock数据
   - provider字段为"mock"

2. **Qwen Provider** (API key已配置):
   - HTTP 200
   - 返回真实API结果
   - provider字段为"qwen"

3. **Qwen Provider** (API key未配置):
   - HTTP 503
   - 返回明确的错误信息

4. **OpenAI Provider** (API key已配置):
   - HTTP 200
   - 返回真实API结果
   - provider字段为"openai"

5. **OpenAI Provider** (API key未配置):
   - HTTP 503
   - 返回明确的错误信息

6. **统一返回格式**:
   - 所有成功响应包含: `provider`, `model`, 以及特定字段
   - 所有错误响应包含: `error`, `provider`, `message`

---

**文档版本**: 1.0  
**创建日期**: 2026-02-05
