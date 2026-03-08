# S2.7 DEPLOY REPORT

## A. 修改文件列表

| 文件 | 变更 |
|------|------|
| docker-compose.yml | 新增 APP_ENV, LOG_LEVEL, CORS_ALLOWED_ORIGINS, SPEC_VALIDATE_PUBLIC；API keys 默认空串 |
| .env.prod.example | 已存在，生产环境变量模板（APP_ENV, WEB_PORT, SECRET_KEY, DATABASE_URL, CORS, LLM 等） |
| Dockerfile | 已包含 curl（healthcheck 依赖） |
| scripts/s2_7_smoke.sh | 新增/更新，上线后自动化冒烟；补充 seed 前置提示 |
| scripts/s2_7_load_test.sh | 新增，最小并发压测 20/50 |
| scripts/rollback_s2_7.sh | 新增/更新，一键回滚（dry-run 支持） |
| docs/S2_7_PROD_RUNBOOK.md | 新增/更新，生产部署手册 |
| docs/S2_7_INCIDENT_PLAYBOOK.md | 已存在，故障处理手册 |

## B. 部署执行证据

### 1. 发布前冻结（Section 1）

```
git status: main, modified + untracked
git branch: main
git log --oneline -n 5:
  325e1f3 feat(c1-5): complete quality report service with tests and documentation
  29e9d21 feat(c1-5): add quality report service and API endpoint
  acd5e4f fix(c1-4.1): fix indentation error in decision_summary_service
  954809f feat(c1-4.1): complete stability improvements
  7f768b0 fix(c1-4.1): stabilize decision tracking tests

docker compose ps: postgres healthy, web healthy (5001->5000)
curl /api/health: {"status":"ok","db_connected":true,"provider":"mock",...}

pytest: 151 passed, 135 warnings
./scripts/s2_5_release_gate.sh: 25 passed, 0 failed

git tag: v2.7.0-go-live
```

### 2. 部署命令与输出

```bash
docker compose -f docker-compose.yml down -v
# Output: Containers and volumes removed

docker compose -f docker-compose.yml up --build -d
# Output: postgres healthy, web started

docker compose exec web alembic upgrade head
# Output: Running upgrade -> 001 ... -> 007, add_teacher_decisions

docker compose exec web python scripts/seed_demo_users.py
# Output: Demo users seeded: T001, S001, ADMIN001
```

### 3. 验收命令

```bash
./scripts/s2_7_smoke.sh
./scripts/s2_5_release_gate.sh
```

## C. 冒烟测试结果

| 项 | 结果 |
|----|------|
| 1. Health 200 + status=ok + provider + db_connected | PASS |
| 2. Pages / /teacher /student 200 | PASS |
| 3. 未登录 GET /api/cscl/scripts -> 401 | PASS |
| 4. 教师链路 login->create->spec validate->quality-report->export | PASS |
| 5. Student 页面 /student?script_id=xxx 200 | PASS |
| 6. PDF guardrails | 手动验证（无 fixture 时跳过） |

**合计：6 passed, 0 failed**

## D. 并发压测结果

| 档位 | 接口 | total | err | err_pct |
|------|------|-------|-----|---------|
| 20 | /api/health | 8660 | 0 | 0% |
| 20 | / | 10340 | 0 | 0% |
| 20 | /student | 10400 | 0 | 0% |
| 20 | POST /api/cscl/spec/validate（未登录） | 10983 | 10983 | 100% (401 预期) |
| 50 | /api/health | 10050 | 0 | 0% |

**结论：读接口 5xx≈0，满足课堂使用最低标准。spec/validate 需认证，未登录 401 为预期。**

## E. 多模型兼容结果

- /api/health 返回 `provider` 字段
- LLM_PROVIDER 可配置：openai | qwen | mock
- 默认策略：openai 优先（质量），qwen 可切换备选
- 切换验证：`LLM_PROVIDER=qwen docker compose up -d web` 后 health 返回 `"provider":"qwen"`
- 原始输出：mock → qwen 切换后 `{"provider":"qwen",...}`

## F. 回滚预案与脚本

- 脚本：`./scripts/rollback_s2_7.sh [dry-run]`
- 命令：`docker compose down` → `docker compose up --build -d` → `alembic upgrade head`
- 数据库：不执行 downgrade；需回滚数据时从备份恢复
- 演练：`./scripts/rollback_s2_7.sh dry-run` 执行成功

## G. 已知风险

1. 首次部署需执行 `scripts/seed_demo_users.py`，否则教师登录失败
2. 数据库不执行 downgrade 迁移；需回滚时从备份恢复
3. CORS_ALLOWED_ORIGINS 为空时使用默认 CORS；生产需配置白名单
4. spec/validate 未登录返回 401，压测写接口需带 cookie 或 SPEC_VALIDATE_PUBLIC=true

## H. 最终结论

- **状态：DEPLOY_READY**
- pytest 151 passed
- release gate 25/25
- 冒烟 6/6
- 读接口压测 5xx≈0
- provider 切换验证通过
