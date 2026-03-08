# S2.8 ENUM REGRESSION HOTFIX REPORT

## 1) 修改文件清单

| 文件 | 变更 |
|------|------|
| app/models.py | 为 UserRole、SubmissionStatus 三处 Enum 字段添加 `name=` 与 `values_callable` |

## 2) 每个 enum 字段的修复前后对照

| 模型.字段 | 修复前 | 修复后 |
|-----------|--------|--------|
| User.role | `Enum(UserRole, values_callable=lambda x: [e.value for e in x])` | `Enum(UserRole, values_callable=lambda enum_cls: [e.value for e in enum_cls], name='userrole')` |
| Submission.status | `Enum(SubmissionStatus, values_callable=lambda x: [e.value for e in x])` | `Enum(SubmissionStatus, values_callable=lambda enum_cls: [e.value for e in enum_cls], name='submissionstatus')` |
| AuditLog.role | `Enum(UserRole, values_callable=lambda x: [e.value for e in x])` | `Enum(UserRole, values_callable=lambda enum_cls: [e.value for e in enum_cls], name='userrole')` |

说明：`name=` 与 migrations 中已有 PostgreSQL enum type 一致；`values_callable` 保证写入 `value`（小写），避免写入 `name`（大写如 PENDING）。

## 3) 执行命令清单

```bash
docker compose down -v
docker compose up --build -d
sleep 15
docker compose exec web alembic upgrade head
docker compose exec web python scripts/seed_demo_users.py
docker compose exec web python -m pytest tests/test_auth_rbac.py::test_unauthorized_teacher_write_endpoint -q
docker compose exec web python -m pytest tests/ -q
./scripts/s2_5_release_gate.sh
```

## 4) 关键结果

### pytest 总结行
```
151 passed, 135 warnings in 30.31s
```

### release gate 总结行
```
TOTAL: 25 passed, 0 failed
```

## 5) 最终结论

- **状态：DEPLOY_READY**
- 0 failed, 0 errors
- 未改动 i18n、UI 配色、信息架构、PDF 提取逻辑
