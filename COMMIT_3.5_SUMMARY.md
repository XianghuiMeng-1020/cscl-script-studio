# Commit 3.5：DB 存储最小走通 - 完成总结

## 修改文件列表

### 新增文件
1. `app/repositories/__init__.py` - Repository 工厂函数
2. `app/repositories/assignment_repository.py` - Assignment Repository (DB + JSON)
3. `app/repositories/submission_repository.py` - Submission Repository (DB + JSON)
4. `app/repositories/rubric_repository.py` - Rubric Repository (DB + JSON)
5. `app/repositories/user_repository.py` - User Repository (DB + JSON)

### 修改文件
1. `app/models.py` - 添加 Rubric 模型，扩展 Assignment 和 Submission 模型字段
2. `app/routes/api.py` - 修改以下端点使用 Repository：
   - `POST /api/demo/init` - 使用 Repository，支持幂等（清表再插入）
   - `GET /api/submissions` - 使用 Repository
   - `GET /api/stats/teacher` - 使用 Repository
   - `GET /api/stats/student/<student_id>` - 使用 Repository
   - `GET /api/health` - 添加 `use_db_storage` 和 `db_connected` 字段
3. `migrations/versions/001_initial_schema.py` - 添加 rubrics 表，扩展 assignments 和 submissions 表字段

## 新增/变更 env（无）

所有环境变量已在之前 commit 中定义：
- `USE_DB_STORAGE` - 控制使用 DB 还是 JSON 存储
- `DATABASE_URL` - 数据库连接字符串

## 实现要点

1. **Repository 模式**：通过 `USE_DB_STORAGE` 开关自动选择 DBRepo 或 JsonRepo
2. **幂等性**：demo init 通过清表再插入实现幂等
3. **兼容性**：Submission.to_dict() 包含 JSON 格式的兼容字段（feedback, rubric_scores 等）
4. **外键约束**：demo init 在 DB 模式下会创建必要的用户（S001, S002）

## 验收步骤

### A) Docker + Postgres 路径（必须）

```bash
# 1. 设置环境变量
export USE_DB_STORAGE=true
export DATABASE_URL=postgresql://postgres:postgres@postgres:5432/teacher_in_loop

# 2. 清理并重建
docker compose down -v
docker compose up --build -d

# 3. 运行迁移
docker compose exec web alembic upgrade head

# 4. 初始化 demo 数据
curl -X POST http://localhost:5001/api/demo/init

# 5. 验证 teacher 页面能看到 pending submissions
curl http://localhost:5001/teacher

# 6. 验证 student 页面能看到 submissions
curl http://localhost:5001/student

# 7. 验证 health check
curl http://localhost:5001/api/health
# 应返回: {"status":"ok","db_configured":true,"db_connected":true,"use_db_storage":true,...}
```

### B) JSON fallback 路径（必须）

```bash
# 1. 设置环境变量
export USE_DB_STORAGE=false

# 2. 重启服务
docker compose restart web

# 3. 重跑 demo init
curl -X POST http://localhost:5001/api/demo/init

# 4. 验证 teacher/student 流程仍正常
curl http://localhost:5001/teacher
curl http://localhost:5001/student
```

## 关键输出示例

### Health Check (DB 模式)
```json
{
  "status": "ok",
  "db_configured": true,
  "db_connected": true,
  "use_db_storage": true,
  "provider": "qwen"
}
```

### Demo Init 响应
```json
{
  "message": "Demo data initialized successfully"
}
```

### Submissions API (pending)
```json
[
  {
    "id": "SUB001",
    "assignment_id": "A001",
    "student_id": "S001",
    "student_name": "John Smith",
    "content": "...",
    "status": "pending",
    "submitted_at": "2025-02-05T...",
    ...
  }
]
```

## 注意事项

1. **Feedback 数据**：在 DB 模式下，feedback 和 rubric_scores 存储在独立的 Feedback 表中，Repository 会自动关联查询
2. **用户创建**：DB 模式下 demo init 会创建 S001 和 S002 用户以满足外键约束
3. **幂等性**：重复执行 demo init 不会产生重复数据（先清表再插入）
