# S2.18 收口修复报告

## 1. 修改文件清单

1. `app/services/cscl_llm_provider.py` - Provider 选择单点化
2. `app/services/cscl_pipeline_service.py` - Fail-fast 和 fallback retry 逻辑
3. `app/routes/cscl.py` - HTTP 状态码映射
4. `app/routes/api.py` - Health 端点使用统一选择逻辑
5. `app/config.py` - 配置默认值更新
6. `.env.example` - 环境变量示例更新
7. `docker-compose.yml` - Docker 配置默认值更新
8. `tests/test_s2_18_provider_selection.py` - 测试更新

## 2. 每个文件关键改动点

### app/services/cscl_llm_provider.py

1. **新增 `_get_config_value()`**: 统一配置读取优先级（current_app.config > os.environ > Config 默认）
2. **新增 `is_provider_runnable()`**: 统一 provider 可运行性检查，返回 `{provider, runnable, reason}`
   - OpenAI: OPENAI_ENABLED=true AND (OPENAI_IMPLEMENTED=true OR LLM_ALLOW_UNIMPLEMENTED_PRIMARY=true) AND OPENAI_API_KEY 非空
   - Qwen: QWEN_ENABLED=true AND QWEN_IMPLEMENTED=true AND QWEN_API_KEY 非空
3. **重构 `select_runnable_provider()`**: 返回详细状态字典 `{ready, provider, reason, primary, fallback, strategy, checks}`
   - 单点选择逻辑
   - 避免 primary==fallback 时的重复尝试
4. **更新 `get_llm_provider_status()`**: 使用 `select_runnable_provider()` 作为单点选择
5. **更新 `get_cscl_llm_provider()`**: 使用 `select_runnable_provider()` 结果

### app/services/cscl_pipeline_service.py

1. **Fail-fast 检查**: 在 planner 前调用 `select_runnable_provider()`，ready=false 时立即返回 503，stages=[]
2. **错误归类**: 识别 provider-not-ready 错误模式（"not implemented", "not fully implemented", "provider not runnable", "api key missing", "disabled"）
3. **Fallback retry 逻辑**: 
   - 只在 fallback 存在、fallback!=primary、且 fallback runnable 时重试
   - 使用 `attempted_providers` set 避免重复尝试
   - 记录 stage_attempts
4. **修复导入**: 从 `cscl_llm_provider` 导入 `is_provider_runnable` 和 `select_runnable_provider`

### app/routes/cscl.py

1. **HTTP 状态码映射**: 按 `code` 字段映射 HTTP 状态码
   - `LLM_PROVIDER_NOT_READY` -> 503
   - `PIPELINE_FAILED` -> 422
2. **保持 JSON 结构稳定**: 返回字段保持前端兼容

### app/routes/api.py

1. **使用统一选择逻辑**: `/api/health` 调用 `get_llm_provider_status()`（内部使用 `select_runnable_provider()`）
2. **暴露字段**: `llm_provider_ready`, `llm_provider_name`, `llm_provider_reason`, `llm_primary`, `llm_fallback`, `llm_strategy`

### app/config.py

1. **默认值更新**: 
   - `LLM_PROVIDER_PRIMARY` 默认从 `'openai'` 改为 `'qwen'`
   - `LLM_PROVIDER_FALLBACK` 默认从 `'qwen'` 改为 `'openai'`
   - 新增 `QWEN_ENABLED` 和 `QWEN_IMPLEMENTED` 配置项（默认 true）

### .env.example

1. **更新默认值**: `LLM_PROVIDER_PRIMARY=qwen`, `LLM_PROVIDER_FALLBACK=openai`
2. **新增配置项**: `QWEN_ENABLED=true`, `QWEN_IMPLEMENTED=true`

### docker-compose.yml

1. **更新默认值**: `LLM_PROVIDER_PRIMARY=qwen`, `LLM_PROVIDER_FALLBACK=openai`
2. **新增环境变量**: `QWEN_ENABLED`, `QWEN_IMPLEMENTED`, `LLM_ALLOW_UNIMPLEMENTED_PRIMARY`

### tests/test_s2_18_provider_selection.py

1. **更新测试**: 适配新的 `select_runnable_provider()` 返回格式（字典而非元组）
2. **新增测试**: `test_pipeline_no_duplicate_retry_when_primary_equals_fallback` - 验证不重复尝试相同 provider

## 3. 测试结果摘要

### 代码编译检查
- ✅ 所有 Python 文件编译通过
- ✅ 无语法错误

### 待运行测试（需要 pytest 环境）

1. `test_select_runnable_provider_never_picks_unimplemented_openai` - 验证不选择未实现的 OpenAI
2. `test_pipeline_returns_503_when_no_runnable_provider` - 验证返回 503 + stages=[]
3. `test_pipeline_no_duplicate_retry_when_primary_equals_fallback` - 验证不重复 retry
4. `test_health_exposes_provider_readiness_fields` - 验证 health 端点字段

## 4. 验收命令输出关键片段

### 代码格式检查
```bash
python3 -m py_compile app/services/cscl_llm_provider.py app/services/cscl_pipeline_service.py app/routes/cscl.py app/routes/api.py
# 结果: 无错误
```

### 待执行测试命令
```bash
# 运行 S2.18 测试
python3 -m pytest -q tests/test_s2_18_provider_selection.py

# 预期输出:
# test_select_runnable_provider_never_picks_unimplemented_openai PASSED
# test_pipeline_returns_503_when_no_runnable_provider PASSED
# test_pipeline_no_duplicate_retry_when_primary_equals_fallback PASSED
# test_health_exposes_provider_readiness_fields PASSED
```

### 待执行验收命令
```bash
# 1. Health 端点检查
curl -s http://localhost:5001/api/health | jq '{llm_provider_ready, llm_provider_name, llm_provider_reason, llm_primary, llm_fallback, llm_strategy}'

# 2. Provider 不可用场景
# 设置: QWEN_API_KEY='', OPENAI_ENABLED=false
curl -X POST http://localhost:5001/api/cscl/scripts/{script_id}/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"spec": {...}}' \
  -b cookies.txt

# 预期: HTTP 503, {"code": "LLM_PROVIDER_NOT_READY", "stages": []}

# 3. Provider 可用场景
# 设置: QWEN_API_KEY='test-key', QWEN_ENABLED=true, QWEN_IMPLEMENTED=true
# 预期: 成功或业务错误，不应是 "not implemented" 的 422
```

## 5. 若仍有未通过项，最小后续修复计划

1. **如果测试失败**: 检查环境变量设置和 config reload 逻辑
2. **如果 health 端点不一致**: 确保 `get_llm_provider_status()` 正确使用 `select_runnable_provider()`
3. **如果 pipeline 仍创建 pending stage**: 检查 fail-fast 逻辑中的 `db.session.rollback()` 是否执行
4. **如果出现重复 retry**: 检查 `attempted_providers` set 逻辑
5. **如果配置读取错误**: 检查 `_get_config_value()` 的 Flask context 处理

## 关键实现点

✅ Provider 选择单点化：`select_runnable_provider()` 作为唯一选择入口
✅ Fail-fast：provider 不可用时立即返回 503，不创建 pending stage
✅ 避免重复 retry：primary==fallback 时不重试
✅ 统一逻辑：health 和 pipeline 使用同一套选择逻辑
✅ 默认配置：primary=qwen, fallback=openai
