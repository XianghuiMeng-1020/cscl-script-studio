# S2.7 Production Runbook

## 1. 前置条件

- Docker & docker compose 已安装
- 生产数据库 PostgreSQL 可访问
- `.env` 已从 `.env.prod.example` 复制并填写

## 2. 部署命令

```bash
# 1. 拉取代码
git fetch
git checkout v2.7.0-go-live

# 2. 复制环境变量
cp .env.prod.example .env
# 编辑 .env，填写 SECRET_KEY、DATABASE_URL、CORS_ALLOWED_ORIGINS

# 3. 停止旧服务
docker compose -f docker-compose.yml down -v

# 4. 构建并启动
docker compose -f docker-compose.yml up --build -d

# 5. 等待健康
sleep 30
docker compose ps
docker compose logs web --tail=100

# 6. 数据库迁移
docker compose exec web alembic upgrade head

# 6. 种子用户（首次部署，冒烟前必须执行）
docker compose exec web python scripts/seed_demo_users.py

# 7. 健康检查
curl -s http://localhost:5001/api/health | jq .
```

## 3. 验收命令

```bash
./scripts/s2_7_smoke.sh
./scripts/s2_5_release_gate.sh
```

## 4. 回滚

```bash
./scripts/rollback_s2_7.sh
# 或 dry-run: ./scripts/rollback_s2_7.sh dry-run
```

## 5. 关键端口

- 外部: WEB_PORT=5001
- 内部 gunicorn: 5000
- postgres: 5432

## 6. 环境变量必填

- SECRET_KEY (production 必填)
- DATABASE_URL (production 必填)
- CORS_ALLOWED_ORIGINS (生产域名，逗号分隔)
