# LLM Provider抽象层改动总结

**Commit**: LLM Provider抽象层（Commit 2的一部分）  
**日期**: 2026-02-05  
**目标**: 支持Qwen、OpenAI和Mock三种LLM Provider，可通过环境变量切换

---

## 修改的文件列表

### 新增文件
1. `app/services/__init__.py` - Services模块初始化
2. `app/services/llm_provider.py` - LLM Provider抽象层实现
   - `LLMProvider` - 抽象基类
   - `QwenProvider` - Qwen/DashScope实现
   - `OpenAIProvider` - OpenAI/GPT实现
   - `MockProvider` - Mock实现（用于测试）
   - `get_llm_provider()` - Provider工厂函数

3. `scripts/test_llm_providers.sh` - Provider验证脚本

### 修改文件
1. `app.py` - 主要改动：
   - 移除硬编码的OpenAI client初始化
   - 添加`get_provider()`函数（singleton模式）
   - 添加`call_llm_api()`统一调用入口
   - 更新所有AI函数使用统一provider：
     - `ai_check_rubric_alignment()`
     - `ai_analyze_feedback_quality()`
     - `ai_improve_feedback()`
     - `ai_generate_visual_summary()`
     - `ai_generate_video_script()`
     - `ai_suggest_scores()`
   - 更新所有AI API端点，统一错误处理（返回503当LLM未配置）
   - 更新`update_submission_feedback()`处理AI调用错误

2. `.env.example` - 添加LLM Provider配置：
   - `LLM_PROVIDER` - Provider选择（qwen|openai|mock）
   - `QWEN_API_KEY`, `QWEN_BASE_URL`, `QWEN_MODEL` - Qwen配置
   - `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL` - OpenAI配置
   - `MOCK_MODEL` - Mock配置（可选）

---

## 新增/修改的env变量清单

### 必需变量
- `LLM_PROVIDER` - Provider选择，可选值：`qwen` | `openai` | `mock`（默认：`qwen`）

### Qwen配置（当LLM_PROVIDER=qwen时）
- `QWEN_API_KEY` - Qwen API密钥（必需）
- `QWEN_BASE_URL` - Qwen API基础URL（默认：`https://dashscope.aliyuncs.com/compatible-mode/v1`）
- `QWEN_MODEL` - Qwen模型名称（默认：`qwen-plus`）

### OpenAI配置（当LLM_PROVIDER=openai时）
- `OPENAI_API_KEY` - OpenAI API密钥（必需）
- `OPENAI_BASE_URL` - OpenAI API基础URL（可选，默认使用OpenAI官方端点）
- `OPENAI_MODEL` - OpenAI模型名称（默认：`gpt-3.5-turbo`）

### Mock配置（当LLM_PROVIDER=mock时）
- `MOCK_MODEL` - Mock模型名称（可选，默认：`mock-model-v1`）

**.env.example已更新**: ✅ 包含所有配置项和API密钥（已配置）

---

## 三种配置下的curl验证命令

### 配置A: Mock Provider（不需要API key）

```bash
# 设置环境变量
export LLM_PROVIDER=mock
unset QWEN_API_KEY
unset OPENAI_API_KEY

# 启动服务（如果还没启动）
# docker compose up 或 python app.py

# 测试AI端点
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

**预期输出**:
```json
{
  "provider": "mock",
  "model": "mock-model-v1",
  "covered_criteria": ["Argument Clarity", "Evidence Support"],
  "missing_criteria": ["Organization", "Language Expression"],
  "coverage_score": 50,
  "suggestions": ["Consider adding feedback on organization", "Mention language expression"],
  "warnings": ["This is a mock provider response for testing"]
}
```

**HTTP状态码**: `200`

---

### 配置B: Qwen Provider（需要QWEN_API_KEY）

```bash
# 设置环境变量（API key从.env文件读取，不要硬编码）
export LLM_PROVIDER=qwen
# 从.env文件加载（如果使用docker compose，会自动加载.env）
# 或手动设置：
# export QWEN_API_KEY="your-qwen-api-key-here"
export QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export QWEN_MODEL="qwen-plus"
unset OPENAI_API_KEY

# 重启服务以加载新环境变量
# docker compose restart web 或重启python进程

# 测试AI端点
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

**预期输出**（成功时）:
```json
{
  "provider": "qwen",
  "model": "qwen-plus",
  "covered_criteria": ["Argument Clarity", "Evidence Support"],
  "missing_criteria": [],
  "coverage_score": 100,
  "suggestions": []
}
```

**HTTP状态码**: `200`

**如果API key无效或未设置，预期输出**:
```json
{
  "error": "QWEN_API_KEY not configured",
  "provider": "qwen",
  "message": "LLM not configured"
}
```

**HTTP状态码**: `503`

---

### 配置C: OpenAI Provider（需要OPENAI_API_KEY）

```bash
# 设置环境变量（API key从.env文件读取，不要硬编码）
export LLM_PROVIDER=openai
# 从.env文件加载（如果使用docker compose，会自动加载.env）
# 或手动设置：
# export OPENAI_API_KEY="your-openai-api-key-here"
export OPENAI_MODEL="gpt-3.5-turbo"
unset QWEN_API_KEY

# 重启服务以加载新环境变量
# docker compose restart web 或重启python进程

# 测试AI端点
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

**预期输出**（成功时）:
```json
{
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "covered_criteria": ["Argument Clarity", "Evidence Support"],
  "missing_criteria": [],
  "coverage_score": 100,
  "suggestions": []
}
```

**HTTP状态码**: `200`

**如果API key无效或未设置，预期输出**:
```json
{
  "error": "OPENAI_API_KEY not configured",
  "provider": "openai",
  "message": "LLM not configured"
}
```

**HTTP状态码**: `503`

---

## 自动化验证脚本

运行完整验证：

```bash
# 确保服务正在运行
# docker compose up 或 python app.py

# 运行验证脚本
./scripts/test_llm_providers.sh
```

脚本会依次测试：
1. Mock provider（应返回200 + mock数据）
2. Qwen provider（应返回200 + qwen数据，或503如果API key无效）
3. OpenAI provider（应返回200 + openai数据，或503如果API key无效）
4. 未配置provider（应返回503 + 错误消息）

---

## 统一返回格式

所有AI端点现在返回统一格式：

### 成功响应
```json
{
  "provider": "qwen|openai|mock",
  "model": "model-name",
  "content": "...",  // 或特定字段（如covered_criteria, improved_feedback等）
  "warnings": ["optional warning messages"]
}
```

### 错误响应（HTTP 503）
```json
{
  "error": "QWEN_API_KEY not configured",
  "provider": "qwen",
  "message": "LLM not configured"
}
```

---

## 影响的API端点

以下端点已更新为使用统一Provider并返回统一格式：

1. `POST /api/ai/check-alignment` - 反馈对齐检查
2. `POST /api/ai/analyze-quality` - 反馈质量分析
3. `POST /api/ai/improve-feedback` - 反馈改进
4. `POST /api/ai/generate-summary` - 视觉摘要生成
5. `POST /api/ai/generate-script` - 视频脚本生成
6. `POST /api/ai/suggest-scores` - 评分建议
7. `PUT /api/submissions/<id>/feedback` - 提交反馈（内部调用AI）

---

## 行为约束验证

✅ **Provider未配置时返回503**: 如果`LLM_PROVIDER=qwen`但`QWEN_API_KEY`未设置，返回503 + JSON错误  
✅ **统一返回格式**: 所有AI端点返回包含`provider`、`model`、`content`/特定字段、`warnings`  
✅ **Mock provider无需key**: Mock provider不需要任何API key，始终返回假数据  
✅ **错误信息可读**: 错误响应包含明确的错误消息和provider信息  

---

## 快速测试命令（三种配置）

### 1. Mock配置测试
```bash
export LLM_PROVIDER=mock
unset QWEN_API_KEY OPENAI_API_KEY
curl -X POST http://localhost:5000/api/ai/check-alignment \
  -H "Content-Type: application/json" \
  -d '{"feedback":"test","rubric_criteria":[]}' | jq '.provider'
# 预期: "mock"
```

### 2. Qwen配置测试
```bash
# 确保.env文件中已设置QWEN_API_KEY
export LLM_PROVIDER=qwen
# docker compose会自动加载.env，或手动source .env
unset OPENAI_API_KEY
curl -X POST http://localhost:5000/api/ai/check-alignment \
  -H "Content-Type: application/json" \
  -d '{"feedback":"test","rubric_criteria":[]}' | jq '.provider'
# 预期: "qwen"
```

### 3. OpenAI配置测试
```bash
# 确保.env文件中已设置OPENAI_API_KEY
export LLM_PROVIDER=openai
# docker compose会自动加载.env，或手动source .env
unset QWEN_API_KEY
curl -X POST http://localhost:5000/api/ai/check-alignment \
  -H "Content-Type: application/json" \
  -d '{"feedback":"test","rubric_criteria":[]}' | jq '.provider'
# 预期: "openai"
```

---

## 注意事项

1. **环境变量生效**: 修改环境变量后需要重启服务（Docker或Python进程）
2. **API key安全**: 
   - ⚠️ **重要**: `.env.example`中只包含占位符，不包含真实API key
   - 实际使用时，复制`.env.example`到`.env`并填入真实API key
   - `.env`文件已在`.gitignore`中，不会被提交到仓库
   - **不要**将真实API key提交到任何可push的文件中
3. **Mock provider**: 用于测试和复现，返回固定结构的假数据，不调用真实API
4. **错误处理**: 所有AI端点现在统一返回503状态码当LLM未配置时，前端应处理此错误
5. **本地配置**: 在本地`.env`文件中配置API key即可运行，无需修改代码

---

**文档版本**: 1.0  
**创建日期**: 2026-02-05
