# S2.10 GO-LIVE Checklist（逐项勾选）

**硬性规则**：任一项未勾选即不得给出 GO_LIVE_APPROVED。

## 0) 核心目标
- [ ] A. 本地可稳定运行（可重复）
- [ ] B. 教师端/学生端所有功能可用（不删功能）
- [ ] C. 三语言全量一致切换（zh-CN / zh-TW / en）
- [ ] D. GPT 主、Qwen 副，fallback 逻辑可验证
- [ ] E. 生成内容质量有可审计证据
- [ ] F. 并发下关键链路稳定（课堂可用）
- [ ] G. 可回滚、可观测、可复现
- [ ] H. 零截图依赖

## 1) 静态门禁
- [ ] 2.1 端口 5001→5000，healthcheck 使用 `/api/health`；health 返回含 status, db_connected, provider, auth_mode, rbac_enabled, llm_primary, llm_fallback, llm_strategy
- [ ] 2.2 LLM_PROVIDER_PRIMARY=openai，LLM_PROVIDER_FALLBACK=qwen；fallback 仅 timeout/429/5xx/连接；401/403/参数不 fallback；日志含 request_id, primary_provider, final_provider, fallback_triggered, error_type, latency_ms
- [ ] 2.3 i18n 三语 key 无缺失；无混语残留
- [ ] 2.4 不对用户暴露 Spec 等主文案；主操作区有 做什么/为什么/完成后得到什么/下一步；首页双入口等权
- [ ] 2.5 文档提取返回用户可读错误；normalize_text 无 %PDF/xref/obj/stream 污染；简繁英提取与最小长度检查

## 2) 动态门禁
- [ ] 3.1 基线启动：docker compose down -v；up --build -d；alembic upgrade head；seed_demo_users.py；health 200
- [ ] 3.2 教师端 E2E：登录→创建活动→上传文档→教学目标检查→生成→质量报告→发布/导出→决策时间线
- [ ] 3.3 学生端 E2E：登录→dashboard→有 script_id 加载活动/无 script_id 空状态→401/403/404 用户可读提示→提交/继续可操作
- [ ] 3.4 未登录受限 API 返回 401/403；教师/学生权限不串权；错误返回 code+message 不泄露堆栈

## 3) 质量审计门禁
- [ ] `scripts/s2_10_quality_audit.sh` 已执行，`outputs/s2_10/quality_audit.json` 存在
- [ ] 五维均 pass：结构完整性、语言可读性、课程对齐度、可执行性、安全/不当输出过滤

## 4) 并发门禁
- [ ] `scripts/s2_10_concurrency_gate.sh` 已执行，`outputs/s2_10/concurrency_report.json` 存在
- [ ] 5xx 比例 < 0.5%；P95（health/page）< 1500ms；关键写错误率 < 1%

## 5) 自动化测试门禁
- [ ] `python -m pytest tests/ -q` 全绿（0 failed, 0 errors）
- [ ] `./scripts/s2_5_release_gate.sh` 全绿
- [ ] `./scripts/s2_9_verify_provider_fallback.sh` 全绿
- [ ] `./scripts/s2_10_quality_audit.sh` 全维 pass
- [ ] `./scripts/s2_10_concurrency_gate.sh` 达标

## 6) 交付物
- [ ] `scripts/s2_10_final_go_live_gate.sh`
- [ ] `docs/S2_10_GO_LIVE_CHECKLIST.md`（本文件）
- [ ] `docs/S2_10_RUNBOOK_PROD.md`
- [ ] `docs/S2_10_UX_ACCEPTANCE.md`
- [ ] `docs/S2_10_UX_BENCHMARK.md`
- [ ] `outputs/s2_10/final_gate_report.md`
- [ ] `outputs/s2_10/quality_audit.json`
- [ ] `outputs/s2_10/concurrency_report.json`
- [ ] `outputs/s2_10/ux_gate_report.json`

## 7) 回滚与观测
- [ ] `scripts/rollback_s2_10.sh [dry-run]` 可执行；回滚后可恢复上一稳定 tag 并通过 health
- [ ] 日志可检索 request_id 与 fallback 轨迹

## 8) UX 与前端门禁
- [ ] `scripts/s2_10_ux_gate.sh` 全通过；`outputs/s2_10/ux_gate_report.json` overall=pass
- [ ] `scripts/s2_10_task_walkthrough.sh` 教师/学生核心链路 ≥95% 一次成功率
- [ ] `docs/S2_10_UX_BENCHMARK.md` 无 FAIL 项
- [ ] UX 评分表总分 ≥ 4.5/5

## 最终结论（二选一）
- [ ] **GO_LIVE_APPROVED**
- [ ] **GO_LIVE_BLOCKED**（若选此项，必须给出 P0→P1→P2 修复序列）
