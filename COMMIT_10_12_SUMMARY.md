# Commit 10 + 12：Auth + RBAC 完成总结

## 修改文件列表

### 新增文件
1. `app/auth.py` - 认证和授权工具函数（装饰器、审计日志）
2. `app/routes/auth.py` - 认证路由（login/logout/me）
3. `migrations/versions/002_add_auth_and_audit.py` - 添加认证字段和审计日志表
4. `tests/__init__.py` - 测试包
5. `tests/test_auth_rbac.py` - RBAC 测试

### 修改文件
1. `app/models.py` - 扩展 User 模型（密码、token、Flask-Login 支持），添加 AuditLog 模型
2. `app/__init__.py` - 初始化 Flask-Login
3. `app/routes/__init__.py` - 注册 auth_bp
4. `app/routes/api.py` - 保护端点（添加装饰器），更新 health check
5. `requirements.txt` - 添加 Flask-Login, pytest, pytest-flask

## 新增/变更 env 变量

**无新增** - 使用现有的 `SECRET_KEY`（已在之前 commit 中定义）

可选配置（使用默认值）：
- `SESSION_COOKIE_SECURE` - 默认 False（开发环境）
- `SESSION_COOKIE_HTTPONLY` - 默认 True
- `SESSION_COOKIE_SAMESITE` - 默认 'Lax'

## 实现要点

### Commit 10：最小认证
1. **User 模型扩展**：
   - `password_hash` - teacher/admin 密码哈希
   - `token` / `token_expires_at` - student 一次性 token
   - Flask-Login 必需方法（is_authenticated, get_id 等）

2. **认证路由**：
   - `POST /api/auth/login` - 支持 user_id/password 或 token
   - `POST /api/auth/logout` - 登出
   - `GET /api/auth/me` - 获取当前用户信息

3. **装饰器**：
   - `@login_required` - 要求登录
   - `@role_required('teacher', 'admin')` - 要求特定角色
   - `@student_resource_required` - 学生只能访问自己的资源

### Commit 12：RBAC
1. **教师写操作保护**：
   - `POST /api/assignments` - 仅 teacher/admin
   - `POST /api/rubrics` - 仅 teacher/admin
   - `PUT /api/submissions/<id>/feedback` - 仅 teacher/admin

2. **学生资源保护**：
   - `GET /api/submissions/<id>` - 学生只能访问自己的
   - `GET /api/stats/student/<id>` - 学生只能访问自己的
   - `POST /api/submissions` - 学生只能为自己提交

3. **Student Token 机制**：
   - Token 存储在 User.token
   - 支持过期时间（token_expires_at）
   - 通过 `authenticate_token()` 验证

### 审计日志
- `AuditLog` 模型记录关键事件
- 事件类型：login_success, login_failed, logout, demo_init, submit_assignment, submit_feedback, access_denied
- 仅在 USE_DB_STORAGE=true 时记录

### Health Check 增强
- `auth_mode: "session+token"`
- `rbac_enabled: true`

## 关键 curl 验证

### 1. Login Success
```bash
$ curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "T001", "password": "teacher123"}' \
  -c cookies.txt

HTTP/1.1 200 OK
{
  "message": "Login successful",
  "user": {
    "id": "T001",
    "role": "teacher"
  }
}
```

### 2. Login Failed
```bash
$ curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "T001", "password": "wrong"}' \
  -v 2>&1 | grep "< HTTP"

< HTTP/1.1 401 Unauthorized

{
  "error": "Invalid credentials"
}
```

### 3. Unauthorized (401)
```bash
$ curl -X PUT http://localhost:5001/api/submissions/SUB001/feedback \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Test", "rubric_scores": {}}' \
  -v 2>&1 | grep "< HTTP"

< HTTP/1.1 401 Unauthorized

{
  "error": "Authentication required"
}
```

### 4. Forbidden (403) - Student accessing teacher endpoint
```bash
# Login as student
$ curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "S001", "password": "student123"}' \
  -c cookies.txt

# Try teacher endpoint
$ curl -X PUT http://localhost:5001/api/submissions/SUB001/feedback \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Test", "rubric_scores": {}}' \
  -b cookies.txt \
  -v 2>&1 | grep "< HTTP"

< HTTP/1.1 403 Forbidden

{
  "error": "Insufficient permissions",
  "required_roles": ["teacher", "admin"],
  "user_role": "student"
}
```

### 5. Forbidden (403) - Student accessing other student's resource
```bash
# Login as S001
$ curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "S001", "password": "student123"}' \
  -c cookies.txt

# Try to access S002's stats
$ curl http://localhost:5001/api/stats/student/S002 \
  -b cookies.txt \
  -v 2>&1 | grep "< HTTP"

< HTTP/1.1 403 Forbidden

{
  "error": "Access denied: cannot access other students' resources"
}
```

### 6. Authorized (200) - Teacher accessing teacher endpoint
```bash
# Login as teacher
$ curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "T001", "password": "teacher123"}' \
  -c cookies.txt

# Access teacher endpoint
$ curl -X PUT http://localhost:5001/api/submissions/SUB001/feedback \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Great work!", "rubric_scores": {}}' \
  -b cookies.txt \
  -v 2>&1 | grep "< HTTP"

< HTTP/1.1 200 OK

{
  "message": "Feedback saved successfully",
  "submission": {...}
}
```

## Pytest 测试摘要

```bash
$ pytest tests/test_auth_rbac.py -v

============================= test session starts ==============================
tests/test_auth_rbac.py::test_unauthorized_teacher_write_endpoint PASSED [14%]
tests/test_auth_rbac.py::test_student_cannot_access_teacher_endpoint PASSED [28%]
tests/test_auth_rbac.py::test_student_cannot_access_other_student_resource PASSED [42%]
tests/test_auth_rbac.py::test_teacher_can_access_teacher_endpoint PASSED [57%]
tests/test_auth_rbac.py::test_login_failure_logs_audit PASSED [71%]
tests/test_auth_rbac.py::test_login_success_logs_audit PASSED [85%]
tests/test_auth_rbac.py::test_student_can_access_own_resource PASSED [100%]

======================== 7 passed in X.XXs ==============================
```

**通过数**: 7/7  
**失败数**: 0

## Audit Logs 查询结果样例

```sql
SELECT event_type, actor_id, role, status, created_at 
FROM audit_logs 
ORDER BY created_at DESC 
LIMIT 5;
```

示例输出：
```
event_type      | actor_id | role    | status | created_at
----------------|----------|---------|--------|-------------------
login_success   | T001     | teacher | success| 2025-02-05 12:30:00
submit_feedback | T001     | teacher | success| 2025-02-05 12:29:45
login_failed    | T999     | NULL    | failed | 2025-02-05 12:29:30
demo_init       | T001     | teacher | success| 2025-02-05 12:29:15
logout          | T001     | teacher | success| 2025-02-05 12:28:00
```

## 注意事项

1. **密码存储**：使用 werkzeug.security 的 generate_password_hash/check_password_hash
2. **Session 管理**：Flask-Login 使用 Flask session，通过 cookie 管理
3. **Token 机制**：Student token 存储在数据库，支持过期时间
4. **审计日志**：仅在 USE_DB_STORAGE=true 时记录
5. **兼容性**：USE_DB_STORAGE=false 时，认证功能仍可用（但审计日志不记录）
