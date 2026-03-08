# S2.10 生产发布 Runbook

## 部署前条件
- 所有 S2.10 门禁通过（见 `docs/S2_10_GO_LIVE_CHECKLIST.md`）
- 环境变量已配置：`SECRET_KEY`、`DATABASE_URL`、`OPENAI_API_KEY`、`QWEN_API_KEY`（若使用）、`LLM_PROVIDER_PRIMARY`、`LLM_PROVIDER_FALLBACK`

## 部署步骤
1. **拉取代码与镜像**
   ```bash
   git pull origin main
   docker compose pull  # 若使用远程镜像
   ```

2. **停服与重建**
   ```bash
   docker compose down
   docker compose up --build -d
   ```

3. **数据库迁移**
   ```bash
   docker compose exec web alembic upgrade head
   ```

4. **种子用户（可选）**
   ```bash
   docker compose exec web python scripts/seed_demo_users.py
   ```

5. **健康检查**
   ```bash
   curl -s http://localhost:5001/api/health | jq .
   ```
   确认 `status=ok`，`db_connected=true`（若用 DB），`llm_primary`/`llm_fallback` 符合预期。

## 监控要点
- **健康**：定期请求 `/api/health`，告警非 200 或 status≠ok
- **LLM 与 fallback**：日志中检索 `cscl_llm_request`、`request_id`、`fallback_triggered`、`error_type`、`latency_ms`
- **错误率**：5xx 比例 < 0.5%；关键写操作错误率 < 1%
- **响应时间**：P95 页面/health < 1500ms

## 回滚
- **一键回滚（dry-run）**：`./scripts/rollback_s2_10.sh dry-run`
- **实际回滚**：`PREV_TAG=v2.9.0 ./scripts/rollback_s2_10.sh`（或省略 PREV_TAG 仅重启）
- 回滚后验证：`curl -s http://localhost:5001/api/health`

## 故障排查
- 日志：`docker compose logs -f web`
- 检索 request_id：`docker compose logs web | grep request_id`
- 检索 fallback：`docker compose logs web | grep fallback_triggered`
