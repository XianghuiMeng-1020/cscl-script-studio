# 从本地到服务器的部署与回滚

本手册与 **DEPLOY_RUNBOOK.md** 一致，侧重「本地 → 服务器」的步骤与回滚。

---

## 环境变量（服务器必配）

| 变量 | 必填 | 说明 |
|------|------|------|
| `SECRET_KEY` | 是 | 生产必须更换，勿用默认值 |
| `DATABASE_URL` | 使用 DB 时 | 例如 `postgresql://user:pass@host:5432/dbname` |
| `USE_DB_STORAGE` | 建议 true | 使用数据库存储 |
| `REDIS_URL` | 多实例时 | 幂等跨实例，例如 `redis://localhost:6379/0` |
| `APP_ENV` | 建议 | 生产设为 `production` |
| `DEBUG` | 必须 | 生产设为 `false` |
| `CORS_ALLOWED_ORIGINS` | 建议 | 生产填实际前端域名，逗号分隔 |

其余见 **DEPLOY_RUNBOOK.md** 第 1 节。

---

## 启动命令

**开发（本地）**
```bash
export FLASK_APP=wsgi.py
python -m flask run --port 5001
# 或
gunicorn -w 1 -b 0.0.0.0:5001 wsgi:app
```

**生产（服务器）**
```bash
export SECRET_KEY="<生成密钥>"
export USE_DB_STORAGE=true
export DATABASE_URL="..."
export REDIS_URL="redis://..."   # 多实例必配
export APP_ENV=production
export DEBUG=false

gunicorn -w 4 -b 0.0.0.0:5001 --timeout 120 --access-logfile - --error-logfile - wsgi:app
```

---

## 迁移（使用 DB 时）

```bash
export FLASK_APP=wsgi.py
flask db upgrade
```

---

## 健康检查与 Smoke（上线后必做）

```bash
curl -s https://your-server/api/health | jq .
./scripts/release_readiness_check.sh   # BASE_URL 可设为服务器地址
SMOKE=1 ./scripts/release_readiness_check.sh
```

---

## 回滚步骤

1. **版本回退**：切回上一版本（如 `git checkout <tag>`），必要时 `flask db downgrade`（谨慎）。
2. **配置回退**：恢复上一份环境变量或 `.env`。
3. **重启**：重启应用（systemd / Docker / 其他）。
4. **验证**：再次执行健康检查与 `release_readiness_check.sh`。

详见 **DEPLOY_RUNBOOK.md** 第 5 节。

---

*完整清单与故障处理见 **DEPLOY_RUNBOOK.md**。*
