# 上线/回滚手册 (Deploy Runbook)

**版本**: 1.0  
**日期**: 2026-02-09

---

## 1. 环境变量清单

### 必填（生产）

| 变量 | 说明 | 示例 |
|------|------|------|
| `SECRET_KEY` | Flask 会话/CSRF 密钥，生产必须更换 | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | 数据库连接串（使用 DB 时必填） | `postgresql://user:pass@host:5432/dbname` |
| `USE_DB_STORAGE` | 使用 DB 存储用户/作业等 | `true` |

### 可选（按需）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_ENV` | `development` | `production` / `development` |
| `DEBUG` | `false` | 生产务必 `false` |
| `WEB_PORT` | `5001` | 服务监听端口 |
| `DATA_DIR` | `data` | 本地数据目录（作业/日志等） |
| `CORS_ALLOWED_ORIGINS` | 空（允许所有） | 生产建议设具体域名，逗号分隔 |
| `REDIS_URL` | 空 | 配置后幂等跨实例（多 worker/多机） |
| `IDEMPOTENCY_TTL_SECONDS` | `120` | 幂等 key 有效期（秒） |
| `UPLOAD_TIMEOUT_SECONDS` | `120` | 上传超时 |
| `DOCUMENT_MAX_FILE_SIZE_MB` | `10` | 单文件上传上限（MB） |
| `PDF_MAX_PAGES` | `500` | PDF 解析最大页数 |
| `LLM_PROVIDER` | `qwen` | `qwen` / `openai` / `mock` |
| `QWEN_API_KEY` | 空 | Qwen 调用密钥 |
| `QWEN_BASE_URL` | 阿里云兼容地址 | 可覆盖 |
| `OPENAI_API_KEY` | 空 | OpenAI 调用密钥 |
| `OPENAI_BASE_URL` | 空 | 可覆盖 |
| `REQUIRE_LOGIN_FOR_TEACHER` | `true` | 教师端是否强制登录 |
| `REQUIRE_LOGIN_FOR_STUDENT` | `true` | 学生端是否强制登录 |
| `SPEC_VALIDATE_PUBLIC` | `false` | 开发可 `true` 免登录校验 spec |

---

## 2. 启动命令

### 开发（单进程）

```bash
cd /path/to/teacher-in-loop-main
export FLASK_APP=wsgi.py
export FLASK_ENV=development
# 可选: export DATABASE_URL=sqlite:///instance/app.db
# 可选: export USE_DB_STORAGE=true
python -m flask run --port 5001
# 或
gunicorn -w 1 -b 0.0.0.0:5001 wsgi:app
```

### 生产（多 worker）

```bash
export SECRET_KEY="<生成的安全密钥>"
export USE_DB_STORAGE=true
export DATABASE_URL="postgresql://..."
export REDIS_URL="redis://localhost:6379/0"   # 多实例幂等
export APP_ENV=production
export DEBUG=false

gunicorn -w 4 -b 0.0.0.0:5001 --timeout 120 --access-logfile - --error-logfile - wsgi:app
```

### Docker Compose

```bash
docker compose up --build -d
# 等待约 30 秒后做健康检查
```

---

## 3. 健康检查与 Smoke

### 健康检查

```bash
curl -s http://localhost:5001/api/health | jq .
# 期望: "status": "ok", "db_configured", "db_connected", "llm_provider_ready" 等
```

### 发布就绪检查（不跑 smoke）

```bash
./scripts/release_readiness_check.sh
# 期望: 输出 PASS，退出码 0
```

### 完整 Smoke（登录 → 上传 → 列表 → 预检 → 生成）

```bash
# 默认账号 T001 / teacher123（测试环境）
./scripts/smoke_prod_flow.sh

# 或 demo 账号
SMOKE_USER=teacher_demo SMOKE_PASSWORD='Demo@12345' ./scripts/smoke_prod_flow.sh
```

### 带 Smoke 的发布就绪

```bash
SMOKE=1 ./scripts/release_readiness_check.sh
```

---

## 4. 常见故障处理

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 健康检查 502/超时 | 进程未起或端口错误 | 查进程、端口；看 gunicorn/Flask 日志 |
| `db_connected: false` | 数据库不可达或迁移未跑 | 检查 DATABASE_URL、网络；执行迁移见下 |
| `llm_provider_ready: false` | 未配 API Key 或 Key 无效 | 配置 QWEN_API_KEY 或 OPENAI_API_KEY |
| 上传 413 | 文件超过 DOCUMENT_MAX_FILE_SIZE_MB | 告知用户限制或适当调大 |
| 上传/生成很慢或超时 | 大 PDF/LLM 超时 | 调大 UPLOAD_TIMEOUT_SECONDS、gunicorn --timeout |
| 重复点击生成出现多条 run | 未配 Redis 且多 worker | 配置 REDIS_URL 使幂等跨实例 |
| 教师/学生 401 | 未登录或 session 失效 | 重新登录；检查 SECRET_KEY 是否一致（多实例） |

### 数据库迁移（使用 DB 时）

```bash
# 开发/生产
export FLASK_APP=wsgi.py
flask db upgrade
# 或
python -m flask db upgrade
```

---

## 5. 回滚步骤

### 5.1 版本回退

1. 切回上一版本代码（如 `git checkout <previous-tag>`）。
2. 若模型/迁移有变更，评估是否需要执行 `flask db downgrade`（谨慎）。
3. 重启应用：
   ```bash
   # systemd 示例
   sudo systemctl restart teacher-in-loop
   # 或 Docker
   docker compose down && docker compose up -d
   ```

### 5.2 配置回退

1. 恢复上一份环境变量或 `.env`（如备份的 `.env.prod`）。
2. 重启应用使配置生效。

### 5.3 验证回滚

```bash
curl -s http://localhost:5001/api/health | jq .
./scripts/release_readiness_check.sh
# 必要时再跑 SMOKE=1
```

---

## 6. 日志与排障

- 请求级：响应头 `X-Request-Id` 与日志中的 `trace_id` 对应。
- 每条 API 请求会打一行：`trace_id, user_id, endpoint, method, path, status_code, latency_ms, error_code`。
- 500 错误会打完整 traceback，响应体为 JSON 且含 `trace_id`，便于前后端联调。

---

*与 RUN_LOCAL.md、docs/PHASE_C_C1_C2_DELIVERY.md 配合使用。*
