# Phase C — C1 + C2 交付说明

## 1. 修改文件清单

| 类型 | 文件 |
|------|------|
| **C1 幂等** | `app/config.py` — 新增 `REDIS_URL`, `IDEMPOTENCY_TTL_SECONDS` |
| **C1 幂等** | `app/services/pipeline/idempotency.py` — 重写：Redis 优先，无 Redis 时回退内存 |
| **C1 测试** | `tests/test_idempotency.py` — 新建：get/set、双请求同 key、15 次同 key 同 run_id |
| **C2 可观测** | `app/__init__.py` — `before_request` 注入 `g.request_id`/开始时间，`after_request` 打结构化日志、响应头 `X-Request-Id`；500 时记录 traceback 并返回 JSON |
| **C2 错误体** | `app/routes/cscl.py` — 413 使用 `api_error_response`（含 trace_id） |
| **C2 测试** | `tests/test_api_413_and_trace_id.py` — 新建：413 统一 JSON、404 含 trace_id、健康检查含 X-Request-Id |
| **依赖** | `requirements.txt` — 新增 `redis>=4.5.0` |

---

## 2. 关键 diff 摘要

### C1 幂等（跨实例）

- **config**: `REDIS_URL` 默认空（不配则用内存）；`IDEMPOTENCY_TTL_SECONDS` 默认 120。
- **idempotency.py**:
  - `_get_redis()` 懒加载，从 `current_app.config['REDIS_URL']` 连接，失败则标记不可用并回退内存。
  - Key：`idempotency:pipeline:{script_id}:{idempotency_key}`，TTL 从 config 读。
  - `get_cached_run_for_key` / `set_cached_run_for_key`：先试 Redis get/setex，异常则回退内存并打 warning 日志。

### C2 可观测

- **before_request**（仅 `/api/*`）：`g.request_id = uuid4()[:16]`，`g.request_start_time = time.time()`。
- **after_request**（仅 `/api/*`）：响应头 `X-Request-Id`；单行结构化日志：`trace_id, user_id, endpoint, method, path, status_code, latency_ms, error_code`。
- **500 handler**：`logger.error(..., exc_info=True)` 记录完整 traceback；响应体为 B3 格式并带 `trace_id`。

### 413 统一格式

- 上传返回 `FILE_TOO_LARGE` 时改为调用 `api_error_response('FILE_TOO_LARGE', ..., 413, details=...)`，响应含 `success=false, error_code, message, trace_id, details`。

---

## 3. 实测命令与预期输出

在项目根目录执行（需已安装依赖：`pip install -r requirements.txt`）。

### 3.1 回归 + C1/C2 单测

```bash
python3 -m pytest tests/test_cscl_rag_grounding_api.py tests/test_cscl_pipeline_api.py tests/test_idempotency.py tests/test_api_413_and_trace_id.py -v --tb=short
```

**预期**：全部通过（含 `test_upload_file_too_large_returns_413_and_unified_json`、`test_pipeline_run_idempotent_same_key_returns_same_run_id`、`test_idempotency_repeated_same_key_returns_same_run_id`、`test_api_404_returns_trace_id`、`test_api_response_includes_x_request_id_header`）。

### 3.2 发布就绪检查（需服务已起）

```bash
./scripts/release_readiness_check.sh
SMOKE=1 ./scripts/release_readiness_check.sh
```

**预期**：最后输出 `PASS (release readiness checks)` 且退出码 0。

### 3.3 teacher_demo 全链路（需服务 + teacher_demo 账号）

```bash
SMOKE_USER=teacher_demo SMOKE_PASSWORD='Demo@12345' ./scripts/smoke_prod_flow.sh
```

**预期**：输出 `PASS` 且退出码 0。

### 3.4 413 与错误体

```bash
# 健康检查带 X-Request-Id
curl -sI http://localhost:5001/api/health | grep -i x-request-id

# 404 返回 JSON 含 trace_id
curl -s http://localhost:5001/api/nonexistent | jq .

# 413 需上传超限文件（或跑单测）
python3 -m pytest tests/test_api_413_and_trace_id.py::test_upload_file_too_large_returns_413_and_unified_json -v
```

### 3.5 示例日志片段（C2 结构化）

成功请求示例：

```
api_request trace_id=a1b2c3d4e5f6 user_id=T001 endpoint=cscl.upload_course_document method=POST path=/api/cscl/courses/default-course/docs/upload status_code=201 latency_ms=45 error_code=-
```

失败请求示例：

```
api_request trace_id=f6e5d4c3b2a1 user_id=T001 endpoint=cscl.run_pipeline method=POST path=/api/cscl/scripts/xxx/pipeline/run status_code=503 latency_ms=12 error_code=-
```

500 时除上述外还有：

```
api_500 trace_id=... path=/api/... error=... 
Traceback (most recent call last): ...
```

---

## 4. 剩余风险（高/中/低）

| 风险 | 级别 | 说明 |
|------|------|------|
| Redis 未配时多实例幂等无效 | **中** | 未设置 `REDIS_URL` 时仍用进程内内存，多 gunicorn worker/多实例会重复执行。生产若多实例必须配 Redis。 |
| Redis 连接失败只打 warning | **低** | 连接失败会回退内存，不中断请求；需通过监控/日志发现 Redis 不可用。 |
| 并发压测为顺序请求 | **低** | 当前测试为 15 次顺序同 key，真实并发需另做负载测试（如 ab/locust）。 |
| 日志格式与采集 | **低** | 当前为单行文本；若需 JSON 或接入 ELK，可再包一层 formatter 或日志管道。 |

---

*C1 + C2 交付完成。*

---

## Phase C 后续完成项（C3 / C4 / C5）

### C3 预填
- **服务** `app/services/prefill_service.py`：规则提取 course_title、topic、description、learning_outcomes、task_type、expected_output、requirements_text、class_size、duration；空/短文档返回 degraded 与 warnings，不阻塞。
- **路由** `GET /api/cscl/courses/<course_id>/docs/<doc_id>/prefill`：返回 `suggestions`、`warnings`、`degraded`。
- **前端** 文档列表卡片增加「填充建议」按钮，调用 prefill 后 `fillSpecForm` + 跳转 Step 2，提示教师确认或修改。
- **测试** `tests/test_prefill_api.py`。

### C4 前端收口
- **样式** `teacher_cscl_additions.css`：按钮 min-width、disabled 状态、document-actions 弹性布局；窄屏适配。
- **文案** 教师导向：Run Pipeline → 开始生成；Pipeline started → 流程已启动请等待完成；Please validate spec first → 请先完成教学目标验证；Suggestions applied → 已填入建议，请确认或修改后再验证。

### C5 上线/回滚手册
- **文档** `DEPLOY_RUNBOOK.md`：环境变量（必填/可选）、启动命令（dev/prod）、健康检查与 smoke、常见故障、回滚步骤。
