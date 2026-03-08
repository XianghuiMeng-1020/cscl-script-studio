# Changelog — Production Hardening (Phase B)

## 2026-02-09

### B1: 统一 course_id
- **前端** `static/js/teacher.js`: 引入 `DEFAULT_COURSE_ID = 'default-course'`，文档上传/列表/删除与脚本创建均使用该 course_id，保证 pipeline RAG 能检索到同课程文档。
- **测试** `tests/test_cscl_rag_grounding_api.py`: 新增 `test_b1_default_course_unified_upload_list_and_script`，验证 upload → list → 创建 script（同一 course_id）→ 脚本归属正确。

### B2: Pipeline 预检 (preflight)
- **路由** `app/routes/cscl.py`: 新增 `POST /api/cscl/scripts/<script_id>/pipeline/preflight`。校验：script 存在且归属当前用户、spec 必填且通过 SpecValidator、course_id、是否有文档、provider 是否就绪。返回 `success`, `ready`, `error_code`, `message`, `details`（含 `checks`）。
- **测试** `tests/test_cscl_pipeline_api.py`: 新增 `test_pipeline_preflight_200_when_ready`、`test_pipeline_preflight_422_invalid_spec`。

### B3: 统一 API 错误响应（禁止 HTML）
- **工具** `app/utils/api_errors.py`: 新增 `api_error()`、`api_error_response()`、`is_api_request()`，统一错误体格式 `{ success: false, error_code, message, details?, trace_id? }`。
- **应用** `app/__init__.py`: 注册 `@app.errorhandler(404)` 与 `@app.errorhandler(500)`，对 `/api/*` 请求返回 JSON，不再返回 HTML。

### M2: FILE_TOO_LARGE → 413
- **路由** `app/routes/cscl.py`: 上传接口在 `error_code == 'FILE_TOO_LARGE'` 时返回 HTTP 413，响应体含 `success`, `error_code`, `message`, `details`。

### M1: 上传/解析超时与可控上限
- **配置** `app/config.py`: 新增 `UPLOAD_TIMEOUT_SECONDS`、`DOCUMENT_MAX_FILE_SIZE_MB`、`PDF_MAX_PAGES`（均可通过环境变量覆盖）。
- **服务** `app/services/document_service.py`: `MAX_FILE_SIZE` 改为从配置读取；PDF 解析仅处理前 `PDF_MAX_PAGES` 页，避免大文件长时间阻塞。

### M5: 幂等与防双击
- **后端** `app/services/pipeline/idempotency.py`: 新增内存缓存，支持 `Idempotency-Key` 头/体，同一 key 在 TTL 内返回已创建 run。
- **路由** `app/routes/cscl.py`: `run_pipeline` 读取 `Idempotency-Key` 或 `idempotency_key`，命中缓存则直接返回已有 run；成功创建后写入缓存。
- **前端** `static/js/teacher.js`: 进入 `runPipeline()` 即禁用按钮并设 `pipelineRunInProgress`；请求携带 `Idempotency-Key` 与 `idempotency_key`；所有出口与 `finally` 中重置状态。

### Smoke 与发布就绪
- **脚本** `scripts/smoke_prod_flow.sh`: 流程 login → upload → list → create script → preflight → pipeline run，输出 PASS/FAIL，exit 0 仅当全部通过。
- **脚本** `scripts/release_readiness_check.sh`: 检查 health、API 404 返回 JSON、docs 未认证返回 401/403、preflight 存在；可选 `SMOKE=1` 执行完整 smoke。

---

## Phase C（上线前收口）

### C1: 幂等跨实例（Redis）
- **config** `REDIS_URL`, `IDEMPOTENCY_TTL_SECONDS`；**idempotency.py** Redis 优先、无 Redis 时回退内存；多实例下同 Idempotency-Key 返回同一 run_id。
- **测试** `tests/test_idempotency.py`（含同 key 多次请求同 run_id）。

### C2: 可观测（trace_id、结构化日志、500 栈）
- **app/__init__.py**：`before_request` 注入 `g.request_id`/开始时间；`after_request` 打单行结构化日志、响应头 `X-Request-Id`；500 时 `logger.error(..., exc_info=True)` 并返回 JSON 含 trace_id。
- **测试** `tests/test_api_413_and_trace_id.py`（413 统一 JSON、404/健康检查含 trace_id/X-Request-Id）。

### C3: 预填（教师减负）
- **服务** `app/services/prefill_service.py` 规则提取 course_title、topic、description、learning_outcomes、task_type、expected_output、requirements_text、class_size、duration；空/短文档降级提示。
- **路由** `GET /api/cscl/courses/<course_id>/docs/<doc_id>/prefill`。
- **前端** 文档卡片「填充建议」→ 调 prefill → fillSpecForm + 跳 Step 2，提示确认/修改。
- **测试** `tests/test_prefill_api.py`。

### C4: 前端收口
- **样式** 按钮 min-width、状态、document-actions 弹性布局；窄屏适配。
- **文案** 教师导向：开始生成、流程已启动请等待完成、请先完成教学目标验证、已填入建议请确认或修改后再验证。

### C5: 上线/回滚手册
- **DEPLOY_RUNBOOK.md**：环境变量、启动命令、健康检查与 smoke、常见故障、回滚步骤。
- **RUNBOOK_LOCAL_TO_SERVER.md**：本地→服务器要点与回滚。
- **ACCEPTANCE_CHECKLIST.md**：必过项勾选清单。

---

*Phase B + C 完成。后续 Phase D–G 见 PROD_GAP_REPORT.md。*
