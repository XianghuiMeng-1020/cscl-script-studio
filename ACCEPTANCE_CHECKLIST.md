# 上线前验收清单 (Production Hardening)

**目标**: 可稳定给全体学生使用 + 可回滚 + 可观测。  
**日期**: 2026-02-09

---

## 必过项（全部勾选方可上服务器）

### 回归与 Smoke
- [ ] `python3 -m pytest tests/test_cscl_rag_grounding_api.py tests/test_cscl_pipeline_api.py tests/test_idempotency.py tests/test_api_413_and_trace_id.py tests/test_prefill_api.py -v --tb=short` 全部通过
- [ ] `./scripts/release_readiness_check.sh` 输出 PASS，退出码 0
- [ ] `SMOKE=1 ./scripts/release_readiness_check.sh` 通过（或单独运行 `./scripts/smoke_prod_flow.sh`）
- [ ] `SMOKE_USER=teacher_demo SMOKE_PASSWORD='Demo@12345' ./scripts/smoke_prod_flow.sh` 通过（真实 demo 账号）

### 接口与数据
- [ ] GET `/api/health` 返回 `status: ok`
- [ ] POST `/api/cscl/courses/<course_id>/docs/upload`、GET `/api/cscl/courses/<course_id>/docs` 行为未破坏
- [ ] 上传超限文件返回 HTTP 413，响应体含 `success`, `error_code`, `message`, `trace_id`
- [ ] 任意 API 错误均为 JSON，无 HTML 错页；404/500 含 `trace_id`

### 幂等与多实例
- [ ] 配置 `REDIS_URL` 后，多 worker/多实例下同一 Idempotency-Key 返回同一 run_id
- [ ] 重复点击「开始生成」不产生重复 run（前端防双击 + 后端幂等）

### 预填与教师流程
- [ ] GET `/api/cscl/courses/<course_id>/docs/<doc_id>/prefill` 返回建议字段；空/短文档有降级提示
- [ ] 文档列表「填充建议」按钮可填充表单并跳转 Step 2，教师可确认/修改后验证

### 可观测
- [ ] 所有 `/api/*` 响应头含 `X-Request-Id`
- [ ] 请求日志含 `trace_id`, `user_id`, `endpoint`, `status_code`, `latency_ms`
- [ ] 500 时日志含完整 traceback，响应为 JSON

### 文档与回滚
- [ ] `DEPLOY_RUNBOOK.md` 已阅：环境变量、启动命令、健康检查、故障处理、回滚步骤
- [ ] 执行过回滚演练（可选但建议）

---

## 可选验收

- [ ] 真实 PDF 上传 → 列表 → 预填 → 确认 → 生成 全流程走通
- [ ] 移动/窄屏下关键按钮无错位、可点击

---

*勾选完成后可进行部署。*
