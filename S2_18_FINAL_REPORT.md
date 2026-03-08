# S2.18 Final Report: Provider Selection Single Point + Fail-Fast

## 目标
修复 pipeline 仍误用 openai 的阻塞问题。要求 proposal-first，不允许 demo 占位逻辑。

## 完成项

### 1. Provider 选择单点化

**文件**: `app/services/cscl_llm_provider.py`

- ✅ 新增 `select_runnable_provider()` 函数：
  - 单点选择逻辑
  - 返回 `(provider_name, reason)`
  - 默认 primary 是 `qwen`（不是 `openai`）
  - 当 `LLM_ALLOW_UNIMPLEMENTED_PRIMARY=false` 时，OpenAI 必须实现才能运行

- ✅ 修复 `_is_provider_runnable(name)` 函数：
  - OpenAI 在 `OPENAI_ENABLED=false` 或 `OPENAI_IMPLEMENTED=false` 且 `LLM_ALLOW_UNIMPLEMENTED_PRIMARY=false` 时判定为不可运行
  - 明确逻辑：生产模式必须实现，测试模式可允许未实现

- ✅ 更新 `get_llm_provider_status()`：
  - 使用 `select_runnable_provider()` 作为单点选择
  - 返回 `{llm_provider_ready, llm_provider_name, llm_provider_reason}`

- ✅ 更新 `get_cscl_llm_provider()`：
  - 使用 `select_runnable_provider()` 作为单点选择
  - 不再有隐式的 openai 回退

### 2. Pipeline Service Fail-Fast

**文件**: `app/services/cscl_pipeline_service.py`

- ✅ 在 planner 前强制调用 `select_runnable_provider()`
- ✅ 不可运行时返回 `LLM_PROVIDER_NOT_READY`，不创建 pending stage
- ✅ 导入 `_is_provider_runnable` 用于检查

### 3. CSCL 路由 503 映射

**文件**: `app/routes/cscl.py`

- ✅ 将 `LLM_PROVIDER_NOT_READY` 映射为 503
- ✅ 返回 `code=LLM_PROVIDER_NOT_READY`
- ✅ 包含 `details` 字段（selected, fallback, reason）

### 4. 移除所有 openai 默认回退

**已修复的文件**:

1. ✅ `app/config.py`:
   - `LLM_PROVIDER_PRIMARY` 默认从 `'openai'` 改为 `'qwen'`

2. ✅ `docker-compose.yml`:
   - `LLM_PROVIDER_PRIMARY` 默认从 `openai` 改为 `qwen`

3. ✅ `.env.example`:
   - `LLM_PROVIDER_PRIMARY=qwen`
   - `LLM_PRIMARY=qwen`

4. ✅ `app/services/cscl_llm_provider.py`:
   - `select_runnable_provider()` 默认 primary 是 `qwen`
   - 所有 `getattr(Config, 'LLM_PROVIDER_PRIMARY', 'qwen')` 使用 `qwen` 而不是 `openai`

**未修改的文件**（这些文件是其他用途，不影响 CSCL pipeline）:
- `app/services/llm_provider.py` - 这是另一个 LLM provider 系统，不影响 CSCL
- `docker-compose.yml` 中的 `OPENAI_MODEL` - 这是模型名称，不是 provider 选择

### 5. Health 返回 Provider Readiness

**文件**: `app/routes/api.py`

- ✅ `/api/health` 返回：
  - `llm_provider_ready` (bool)
  - `llm_provider_name` (str)
  - `llm_provider_reason` (str)

### 6. 测试

**文件**: `tests/test_s2_18_provider_selection.py`

- ✅ `test_select_runnable_provider_never_picks_unimplemented_openai`: 验证选择逻辑不选择未实现的 OpenAI
- ✅ `test_pipeline_returns_503_when_openai_not_implemented`: 验证 pipeline 返回 503
- ✅ `test_pipeline_no_pending_stage_when_provider_not_ready`: 验证不创建 pending stage
- ✅ `test_health_exposes_provider_readiness_fields`: 验证 health 端点字段

## 变更文件清单

1. `app/services/cscl_llm_provider.py` - Provider 选择单点化
2. `app/services/cscl_pipeline_service.py` - Fail-fast 检查
3. `app/routes/cscl.py` - 503 映射（已存在）
4. `app/routes/api.py` - Health 端点（已存在）
5. `app/config.py` - 默认值从 openai 改为 qwen
6. `docker-compose.yml` - 默认值从 openai 改为 qwen
7. `.env.example` - 默认值从 openai 改为 qwen
8. `tests/test_s2_18_provider_selection.py` - 新测试文件

## 关键 Diff

### app/services/cscl_llm_provider.py

```python
# 新增单点选择函数
def select_runnable_provider() -> tuple[str, str]:
    """S2.18: Single point of provider selection"""
    if os.getenv('LLM_PROVIDER', '').lower() == 'mock':
        return ('mock', 'Mock provider forced via LLM_PROVIDER=mock')
    
    # 默认 primary 是 qwen，不是 openai
    primary_name = os.getenv('LLM_PROVIDER_PRIMARY', getattr(Config, 'LLM_PROVIDER_PRIMARY', 'qwen')).lower()
    fallback_name = os.getenv('LLM_PROVIDER_FALLBACK', getattr(Config, 'LLM_PROVIDER_FALLBACK', 'qwen')).lower()
    
    if _is_provider_runnable(primary_name):
        return (primary_name, f'Primary provider {primary_name} is runnable')
    
    if _is_provider_runnable(fallback_name):
        return (fallback_name, f'Primary {primary_name} not runnable, using fallback {fallback_name}')
    
    return (fallback_name, f'Neither primary {primary_name} nor fallback {fallback_name} is runnable')

# 修复 _is_provider_runnable
def _is_provider_runnable(name: str) -> bool:
    if name == 'openai':
        # 如果 LLM_ALLOW_UNIMPLEMENTED_PRIMARY=false，必须实现
        if Config.LLM_ALLOW_UNIMPLEMENTED_PRIMARY:
            return bool(Config.OPENAI_API_KEY)
        # 生产模式：必须 enabled AND implemented AND has key
        if not Config.OPENAI_ENABLED:
            return False
        if not Config.OPENAI_IMPLEMENTED:
            return False
        if not Config.OPENAI_API_KEY:
            return False
        return True
    # ...
```

### app/services/cscl_pipeline_service.py

```python
# 在 planner 前强制检查
provider_name, reason = select_runnable_provider()
if not _is_provider_runnable(provider_name):
    db.session.rollback()
    return {
        'run_id': None,
        'status': 'provider_not_ready',
        'code': 'LLM_PROVIDER_NOT_READY',
        'stages': [],  # 不创建 pending stage
        # ...
    }
```

### app/config.py

```python
# 默认 primary 从 openai 改为 qwen
LLM_PROVIDER_PRIMARY = os.getenv('LLM_PRIMARY', os.getenv('LLM_PROVIDER_PRIMARY', 'qwen')).lower()
```

## 本地验收命令

### 1. 测试 Provider 选择逻辑

```bash
# 设置环境：OpenAI 未实现，不允许未实现
export LLM_PROVIDER_PRIMARY=openai
export LLM_PROVIDER_FALLBACK=qwen
export OPENAI_ENABLED=true
export OPENAI_IMPLEMENTED=false
export LLM_ALLOW_UNIMPLEMENTED_PRIMARY=false
export QWEN_API_KEY=test-key

# 运行测试
python3 -m pytest tests/test_s2_18_provider_selection.py::test_select_runnable_provider_never_picks_unimplemented_openai -v

# 预期：选择 qwen，不是 openai
```

### 2. 测试 Pipeline 返回 503

```bash
# 设置环境：OpenAI 未实现，无 Qwen key
export LLM_PROVIDER_PRIMARY=openai
export LLM_PROVIDER_FALLBACK=qwen
export OPENAI_ENABLED=true
export OPENAI_IMPLEMENTED=false
export LLM_ALLOW_UNIMPLEMENTED_PRIMARY=false
export QWEN_API_KEY=

# 启动服务后测试
curl -X POST http://localhost:5001/api/cscl/scripts/{script_id}/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"spec": {...}}' \
  -b cookies.txt

# 预期：503，code=LLM_PROVIDER_NOT_READY，stages=[]
```

### 3. 测试 Health 端点

```bash
curl -s http://localhost:5001/api/health | jq '{llm_provider_ready, llm_provider_name, llm_provider_reason}'

# 预期：包含这三个字段
```

### 4. 运行所有 S2.18 测试

```bash
python3 -m pytest tests/test_s2_18_provider_selection.py -v
python3 -m pytest tests/test_s2_18_provider_fallback.py -v
```

## 测试通过摘要

### test_select_runnable_provider_never_picks_unimplemented_openai
- **通过条件**: `provider_name == 'qwen'` 且 `provider_name != 'openai'`
- **验证**: 当 OpenAI 未实现且 `LLM_ALLOW_UNIMPLEMENTED_PRIMARY=false` 时，选择 qwen

### test_pipeline_returns_503_when_openai_not_implemented
- **通过条件**: `resp.status_code == 503` 且 `data['code'] == 'LLM_PROVIDER_NOT_READY'`
- **验证**: Pipeline 在 provider 不可用时返回 503，不创建 pending stage

### test_pipeline_no_pending_stage_when_provider_not_ready
- **通过条件**: `len(data.get('stages', [])) == 0`
- **验证**: 不创建任何 pending stage

### test_health_exposes_provider_readiness_fields
- **通过条件**: 包含 `llm_provider_ready`, `llm_provider_name`, `llm_provider_reason`
- **验证**: Health 端点暴露 provider readiness 信息

## 验收标准

✅ OpenAI 在 `OPENAI_ENABLED=false` 或 `OPENAI_IMPLEMENTED=false` 且 `LLM_ALLOW_UNIMPLEMENTED_PRIMARY=false` 时判定为不可运行

✅ Pipeline 在 planner 前强制调用 `select_runnable_provider()`

✅ 不可运行时返回 503 `LLM_PROVIDER_NOT_READY`，不创建 pending stage

✅ 所有默认 openai 回退已移除（默认 primary 是 qwen）

✅ Health 返回 provider readiness 字段

✅ 测试覆盖所有场景
