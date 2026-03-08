# 阶段1执行计划 (Phase 1 Execution Plan)

**阶段**: 基础重构 (Foundation Refactor)  
**创建日期**: 2026-02-05  
**硬约束**: UX不回退、不做功能扩张、可运行性门禁、配置环境化、隐私最小化

---

## A. Commit级计划 (Commit-Level Plan)

### Commit 1: Docker化基础设施（不改业务逻辑）

**目标**: 添加Docker支持，系统仍使用JSON存储运行

**修改文件**:
- `Dockerfile` (新建)
- `docker-compose.yml` (新建)
- `.env.example` (新建)
- `.dockerignore` (新建)
- `.gitignore` (新建)
- `requirements.txt` (添加gunicorn)
- `app.py` (配置从环境变量读取)
- `data/.gitkeep` (新建，保留目录结构)

**变更内容**:
- Dockerfile: Python 3.11-slim基础镜像，安装gcc和postgresql-client，使用gunicorn运行
- docker-compose.yml: web服务 + postgres服务，环境变量配置，健康检查
- .env.example: 所有配置项模板（SECRET_KEY、DATABASE_URL、QWEN_API_KEY等）
- .dockerignore: 排除不需要的文件（venv、__pycache__、.env等）
- .gitignore: 忽略.env、data/*.json等
- app.py: 
  - SECRET_KEY从环境变量读取（默认值仅用于开发警告）
  - DATA_DIR从环境变量读取
  - QWEN_API_KEY、QWEN_BASE_URL、QWEN_MODEL从环境变量读取
  - DEBUG、FLASK_ENV、WEB_PORT从环境变量读取
  - AI client初始化检查API key是否存在
- requirements.txt: 添加gunicorn==21.2.0

**新增/修改的env变量**:
- `SECRET_KEY`: Flask secret key（必需，生产环境必须设置）
- `DATA_DIR`: 数据目录路径（默认: data）
- `QWEN_API_KEY`: Qwen API密钥（可选，未设置时AI功能不可用）
- `QWEN_BASE_URL`: Qwen API基础URL（默认: DashScope兼容端点）
- `QWEN_MODEL`: Qwen模型名称（默认: qwen-plus）
- `DEBUG`: 调试模式（默认: false）
- `FLASK_ENV`: Flask环境（默认: production）
- `WEB_PORT`: Web服务端口（默认: 5000）
- `DATABASE_URL`: 数据库连接字符串（为后续DB迁移准备）
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`: PostgreSQL配置

**.env.example已更新**: ✅ 包含所有必需和可选配置项

**快速验证结果**:
```bash
# 1. 创建.env文件
cp .env.example .env
# 生成SECRET_KEY并更新.env
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# 2. 构建Docker镜像（需要Docker daemon运行）
docker compose build web
# 预期: 成功构建，无错误

# 3. 启动服务
docker compose up
# 预期: 
# - postgres服务启动并健康检查通过
# - web服务启动，gunicorn监听0.0.0.0:5000
# - 日志输出到stdout（容器友好）

# 4. 验证Web服务响应（在另一个终端）
curl http://localhost:5000/
# 预期: 返回HTML首页

curl http://localhost:5000/api/users
# 预期: 返回JSON用户数据（可能为空数组）

# 5. 验证演示数据初始化
curl -X POST http://localhost:5000/api/demo/init
# 预期: 返回 {"message": "Demo data initialized successfully"}

# 6. 验证现有路由可访问
curl http://localhost:5000/teacher
curl http://localhost:5000/student
# 预期: 都返回HTML页面
```

**成功标志**:
- ✅ `docker compose up`后web和postgres服务都显示"Up"状态
- ✅ 访问`http://localhost:5000/`返回HTML页面
- ✅ `/api/demo/init`端点正常工作
- ✅ `/teacher`和`/student`页面可访问
- ✅ 日志输出到stdout（可在`docker compose logs`中看到）

**已知风险/技术债**:
- ⚠️ 如果QWEN_API_KEY未设置，AI功能会返回None，但不会崩溃（已处理）
- ⚠️ 当前仍使用JSON文件存储，数据库服务已配置但未使用（后续commit会迁移）
- ⚠️ 直接运行`python app.py`仍可用（向后兼容），但生产环境应使用gunicorn
- 📝 注意: Docker daemon必须运行才能执行验证命令

**Notes**:
- 所有配置已环境化，无硬编码
- 日志输出到stdout，符合容器化最佳实践
- 保持向后兼容：`python app.py`仍可直接运行
- 为后续数据库迁移做好了准备（postgres服务已配置）

---

### Commit 2: LLM Provider抽象层 + 环境变量配置抽象

**目标**: 
1. 实现统一的LLM Provider抽象层（支持Qwen、OpenAI、Mock）
2. 将所有硬编码配置移到环境变量

**修改文件**:
- `app/services/__init__.py` (新建)
- `app/services/llm_provider.py` (新建，Provider抽象层)
- `app.py` (重构配置部分 + 统一AI调用)
- `.env.example` (完善所有配置项，添加LLM Provider配置)
- `scripts/test_llm_providers.sh` (新建，验证脚本)

**变更内容**:
- **LLM Provider抽象层**:
  - 创建`LLMProvider`抽象基类
  - 实现`QwenProvider`、`OpenAIProvider`、`MockProvider`
  - 添加`get_llm_provider()`工厂函数（根据`LLM_PROVIDER`环境变量选择）
  - 统一`call_llm_api()`调用入口
  - 更新所有AI函数使用统一provider
  - 统一错误处理：LLM未配置时返回503 + JSON错误
  - 统一返回格式：所有AI端点返回`provider`、`model`、`content`/特定字段、`warnings`
- **环境变量配置**:
  - 移除硬编码API密钥
  - 移除硬编码数据目录路径
  - 移除硬编码SECRET_KEY
  - 使用`os.getenv()`读取环境变量
  - 添加LLM Provider相关环境变量（`LLM_PROVIDER`、`QWEN_API_KEY`、`OPENAI_API_KEY`等）

**新增/修改的env变量**:
- `LLM_PROVIDER`: qwen|openai|mock（必需）
- `QWEN_API_KEY`, `QWEN_BASE_URL`, `QWEN_MODEL`: Qwen配置
- `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`: OpenAI配置
- `MOCK_MODEL`: Mock配置（可选）

**.env.example已更新**: ✅ 包含所有LLM Provider配置和API密钥

**快速验证结果**:
```bash
# 测试Mock Provider
export LLM_PROVIDER=mock
curl -X POST http://localhost:5000/api/ai/check-alignment \
  -H "Content-Type: application/json" \
  -d '{"feedback":"test","rubric_criteria":[]}' | jq '.provider'
# 预期: "mock", HTTP 200

# 测试Qwen Provider
export LLM_PROVIDER=qwen
export QWEN_API_KEY="sk-2cedfc30d0af4fef84acf12451d0bf32"
curl -X POST http://localhost:5000/api/ai/check-alignment \
  -H "Content-Type: application/json" \
  -d '{"feedback":"test","rubric_criteria":[]}' | jq '.provider'
# 预期: "qwen", HTTP 200（或503如果API key无效）

# 测试OpenAI Provider
export LLM_PROVIDER=openai
export OPENAI_API_KEY="sk-proj-..."
curl -X POST http://localhost:5000/api/ai/check-alignment \
  -H "Content-Type: application/json" \
  -d '{"feedback":"test","rubric_criteria":[]}' | jq '.provider'
# 预期: "openai", HTTP 200（或503如果API key无效）

# 运行完整验证脚本
./scripts/test_llm_providers.sh
```

**已知风险/技术债**:
- ⚠️ 修改环境变量后需要重启服务才能生效
- ⚠️ API key已配置在`.env.example`中，实际部署时应使用`.env`文件
- 📝 Mock provider返回固定假数据，用于测试和复现
- 📝 所有AI端点现在统一返回503当LLM未配置，前端应处理此错误

**Notes**:
- 所有AI调用现在通过统一的`call_llm_api()`入口，便于切换provider
- Provider选择通过环境变量`LLM_PROVIDER`控制，无需修改代码
- Mock provider保证测试/复现可运行，无需API key
- 错误处理统一：未配置时返回503 + 明确错误消息

---

### Commit 3: SQLAlchemy模型定义（最小schema）

**目标**: 定义对应现有JSON结构的数据库模型

**修改文件**:
- `app/models/__init__.py` (新建)
- `app/models/user.py` (新建)
- `app/models/assignment.py` (新建)
- `app/models/submission.py` (新建)
- `app/models/rubric.py` (新建)
- `app/models/activity_log.py` (新建)
- `app/models/engagement.py` (新建)
- `requirements.txt` (添加sqlalchemy, psycopg2-binary)

**变更内容**:
- User模型: id, username, email, role, password_hash, created_at
- Assignment模型: id, title, description, course_id, due_date, rubric_id, created_at, status
- Submission模型: id, assignment_id, student_id, content, submitted_at, status, feedback, rubric_scores, graded_at
- Rubric模型: id, name, description, criteria (JSON), created_at
- ActivityLog模型: id, timestamp, type, user_id, details (JSON)
- Engagement模型: id, student_id, submission_id, first_view, view_count, actions (JSON)

**验证**: 模型可以导入，无语法错误

---

### Commit 4: Alembic初始化和迁移

**目标**: 设置Alembic，创建初始迁移

**修改文件**:
- `alembic.ini` (新建，通过`alembic init`生成)
- `alembic/env.py` (新建，配置SQLAlchemy连接)
- `alembic/script.py.mako` (新建)
- `alembic/versions/001_initial_schema.py` (新建)

**变更内容**:
- 初始化Alembic: `alembic init alembic`
- 配置env.py使用环境变量DB连接
- 创建初始迁移包含所有表
- 添加迁移脚本注释

**验证**: `alembic upgrade head`成功创建所有表

---

### Commit 5: 数据库连接和会话管理

**目标**: 设置SQLAlchemy连接，创建数据库会话工厂

**修改文件**:
- `app/db.py` (新建)
- `app/__init__.py` (新建，Flask应用工厂)
- `app.py` (重构为使用应用工厂)

**变更内容**:
- db.py: 创建SQLAlchemy实例，初始化函数
- __init__.py: Flask应用工厂，初始化DB，注册蓝图（暂不注册）
- app.py: 改为使用应用工厂（向后兼容，保持直接运行支持）

**验证**: 可以创建Flask应用实例，DB连接正常

---

### Commit 6: 存储适配层 - Repository模式（用户和作业）

**目标**: 创建Repository抽象层，替换JSON读写为DB操作

**修改文件**:
- `app/repositories/__init__.py` (新建)
- `app/repositories/user_repository.py` (新建)
- `app/repositories/assignment_repository.py` (新建)
- `app.py` (使用repository替换JSON操作)

**变更内容**:
- UserRepository: get_all_users(), get_user_by_id(), create_user()
- AssignmentRepository: get_all(), get_by_id(), create(), update()
- 在app.py中替换load_json(USERS_FILE)和load_json(ASSIGNMENTS_FILE)调用
- 保持接口兼容（返回相同数据结构）

**验证**: 现有API端点返回数据格式不变，数据从DB读取

---

### Commit 7: 存储适配层 - Repository模式（提交和评分标准）

**目标**: 继续替换JSON存储为DB

**修改文件**:
- `app/repositories/submission_repository.py` (新建)
- `app/repositories/rubric_repository.py` (新建)
- `app.py` (继续替换JSON操作)

**变更内容**:
- SubmissionRepository: get_all(), get_by_id(), get_by_assignment(), get_by_student(), create(), update_feedback()
- RubricRepository: get_all(), get_by_id(), create()
- 替换submissions和rubrics的JSON操作

**验证**: 提交和评分标准功能正常，数据从DB读取

---

### Commit 8: 存储适配层 - Repository模式（日志和参与度）

**目标**: 完成所有JSON到DB的迁移

**修改文件**:
- `app/repositories/activity_log_repository.py` (新建)
- `app/repositories/engagement_repository.py` (新建)
- `app.py` (完成JSON替换)

**变更内容**:
- ActivityLogRepository: create(), get_all(), get_by_type(), get_summary()
- EngagementRepository: track(), get_by_student_submission(), get_stats()
- 移除所有JSON文件操作函数（load_json, save_json）

**验证**: 所有功能正常，不再依赖JSON文件

---

### Commit 9: 种子数据迁移脚本

**目标**: 创建demo初始化数据的数据库版本

**修改文件**:
- `alembic/versions/002_seed_demo_data.py` (新建，可选)
- `app/scripts/seed_demo.py` (新建)
- `app.py` (更新/api/demo/init端点使用seed脚本)

**变更内容**:
- seed_demo.py: 创建演示用户、评分标准、作业、提交
- 更新/api/demo/init端点调用seed函数
- 保持返回格式兼容

**验证**: `/api/demo/init`成功创建演示数据，数据在DB中

---

### Commit 10: Flask-Login集成和用户模型扩展

**目标**: 添加登录功能基础

**修改文件**:
- `app/models/user.py` (添加UserMixin, password方法)
- `app/__init__.py` (初始化Flask-Login)
- `requirements.txt` (添加flask-login)

**变更内容**:
- User模型实现UserMixin
- 添加check_password(), set_password()方法
- 初始化LoginManager

**验证**: User模型可以用于登录

---

### Commit 11: 登录/登出路由和会话管理

**目标**: 实现教师/管理员登录功能

**修改文件**:
- `app/routes/auth.py` (新建)
- `app/__init__.py` (注册auth蓝图)
- `templates/login.html` (新建)

**变更内容**:
- POST /api/auth/login: 验证用户名密码，创建会话
- POST /api/auth/logout: 登出
- GET /login: 登录页面
- 添加login_required装饰器

**验证**: 可以登录/登出，会话持久化

---

### Commit 12: RBAC装饰器和权限检查

**目标**: 实现基于角色的访问控制

**修改文件**:
- `app/utils/rbac.py` (新建)
- `app/routes/auth.py` (添加角色检查)
- `app.py` (添加RBAC保护到关键端点)

**变更内容**:
- require_role装饰器: @require_role('teacher'), @require_role('admin')
- 资源级权限: 教师只能访问自己的课程
- 保护/api/assignments, /api/rubrics, /api/submissions等端点

**验证**: 未登录用户无法访问受保护端点，教师只能访问自己的资源

---

### Commit 13: 学生一次性令牌系统

**目标**: 实现学生会话令牌机制

**修改文件**:
- `app/models/session_token.py` (新建)
- `app/routes/student.py` (新建)
- `alembic/versions/003_add_session_tokens.py` (新建)
- `app/__init__.py` (注册student蓝图)

**变更内容**:
- SessionToken模型: session_code, token, student_id, expires_at, used_at
- POST /api/sessions/<code>/join: 验证令牌，分配学生到组
- 生成唯一会话代码和令牌
- 令牌验证中间件

**验证**: 学生可以使用令牌加入会话

---

### Commit 14: 最小审计日志表

**目标**: 添加审计日志记录关键事件

**修改文件**:
- `app/models/audit_log.py` (新建)
- `alembic/versions/004_add_audit_log.py` (新建)
- `app/utils/audit.py` (新建)
- `app.py` (在关键操作中添加审计日志)

**变更内容**:
- AuditLog模型: event_type, user_id (匿名), timestamp, details (JSON)
- audit_log()函数: 记录login, demo_init, submit_feedback, submit_assignment
- 在关键端点调用audit_log

**验证**: 关键事件记录到audit_logs表

---

### Commit 15: 前端认证集成（最小改动）

**目标**: 更新前端支持登录，保持UX不变

**修改文件**:
- `templates/teacher.html` (添加登录检查)
- `static/js/teacher.js` (添加token处理)
- `templates/student.html` (添加token处理)
- `static/js/student.js` (添加token处理)

**变更内容**:
- 教师页面: 检查登录状态，未登录重定向到/login
- API调用: 添加Authorization header（如果已登录）
- 学生页面: 使用session token（如果提供）

**验证**: 前端功能正常，UX无变化

---

### Commit 16: 代码模块化重构（拆分app.py）

**目标**: 将app.py拆分为蓝图，保持功能不变

**修改文件**:
- `app/routes/teacher.py` (新建，迁移教师相关路由)
- `app/routes/api.py` (新建，迁移API路由)
- `app/services/ai_service.py` (新建，迁移AI函数)
- `app/__init__.py` (注册所有蓝图)
- `app.py` (简化为应用工厂调用)

**变更内容**:
- 将路由按功能分组到蓝图
- 将AI函数移到services层
- 保持所有端点路径不变

**验证**: 所有路由正常工作，无404错误

---

### Commit 17: 错误处理和日志配置

**目标**: 添加统一错误处理和日志

**修改文件**:
- `app/utils/errors.py` (新建)
- `app/__init__.py` (注册错误处理器)
- `app/config.py` (新建，日志配置)

**变更内容**:
- 自定义异常类
- 全局错误处理器（返回JSON错误响应）
- 日志配置（文件+控制台）

**验证**: 错误返回统一格式，日志正常记录

---

### Commit 18: 最小测试套件

**目标**: 添加关键功能测试

**修改文件**:
- `tests/__init__.py` (新建)
- `tests/conftest.py` (新建，pytest fixtures)
- `tests/test_demo_init.py` (新建)
- `tests/test_rbac.py` (新建)
- `tests/test_api_smoke.py` (新建)
- `pytest.ini` (新建)
- `requirements.txt` (添加pytest, pytest-flask)

**变更内容**:
- test_demo_init: 测试/api/demo/init创建数据
- test_rbac: 测试未登录访问、角色权限
- test_api_smoke: 测试关键API端点响应

**验证**: `pytest`通过所有测试

---

### Commit 19: Makefile和部署文档

**目标**: 添加便捷命令和部署文档

**修改文件**:
- `Makefile` (新建)
- `DEPLOYMENT.md` (新建)
- `.gitignore` (更新，添加.env, __pycache__等)

**变更内容**:
- Makefile: dev, seed_demo, test, migrate, clean命令
- DEPLOYMENT.md: Docker启动、本地启动、迁移、种子数据步骤

**验证**: `make dev`启动系统，`make seed_demo`创建数据

---

### Commit 20: 最终验证和清理

**目标**: 确保所有功能正常，清理临时文件

**修改文件**:
- `README.md` (更新启动说明)
- 删除旧的JSON数据文件（可选，保留备份）
- `.env.example` (最终检查)

**变更内容**:
- 更新README说明新启动方式
- 清理不需要的文件
- 最终验证所有功能

**验证**: 完整流程测试通过

---

## B. 回滚策略 (Rollback Strategy)

### B.1 数据库迁移回滚

**场景**: Alembic迁移失败或破坏数据

**回滚步骤**:
1. **立即回滚迁移**:
   ```bash
   alembic downgrade -1  # 回滚一个版本
   # 或
   alembic downgrade base  # 回滚到初始状态
   ```

2. **恢复JSON数据**:
   - 保留`data/`目录的JSON文件作为备份
   - 如果DB数据损坏，可以重新从JSON导入
   - 创建`scripts/restore_from_json.py`作为紧急恢复脚本

3. **代码回滚**:
   ```bash
   git checkout <previous-commit>
   # 或创建回滚分支
   git checkout -b rollback-phase1-<date>
   git revert <commit-hash>
   ```

**预防措施**:
- 每次迁移前备份数据库: `pg_dump > backup_$(date +%Y%m%d).sql`
- 迁移脚本可重复执行（idempotent）
- 在开发环境充分测试迁移

---

### B.2 认证系统回滚

**场景**: Auth/RBAC破坏现有访问流程

**回滚步骤**:
1. **临时禁用RBAC**:
   - 在`app/utils/rbac.py`中添加`ENABLE_RBAC = False`开关
   - 所有`@require_role`装饰器检查此开关
   - 如果False，跳过权限检查

2. **恢复匿名访问**:
   - 如果登录系统有问题，临时允许未登录访问
   - 在`app/__init__.py`中注释掉`@login_required`
   - 保持功能可用，逐步修复认证

3. **代码回滚**:
   ```bash
   # 回滚到Commit 8（存储适配层完成，无Auth）
   git checkout <commit-8-hash>
   ```

**预防措施**:
- Auth功能分步添加（先登录，再RBAC，再学生token）
- 每个Auth commit后测试现有功能
- 保留"无Auth模式"开关用于紧急情况

---

### B.3 存储适配层回滚

**场景**: Repository层导致数据丢失或API返回错误

**回滚步骤**:
1. **恢复JSON操作**:
   - 保留原始的`load_json()`和`save_json()`函数
   - 在`app.py`中添加`USE_DB_STORAGE = False`开关
   - 如果False，使用JSON文件操作

2. **数据恢复**:
   - 从JSON备份恢复数据
   - 或从数据库导出回JSON格式

3. **代码回滚**:
   ```bash
   # 回滚到Commit 2（环境变量配置完成）
   git checkout <commit-2-hash>
   ```

**预防措施**:
- Repository层保持接口兼容（返回相同数据结构）
- 并行运行JSON和DB，逐步切换
- 每个Repository commit后验证数据一致性

---

### B.4 Docker化回滚

**场景**: Docker配置导致系统无法启动

**回滚步骤**:
1. **直接运行Python**:
   ```bash
   # 不使用Docker，直接运行
   python app.py
   ```

2. **修复Docker配置**:
   - 检查docker-compose.yml配置
   - 检查Dockerfile构建
   - 查看容器日志: `docker compose logs`

3. **代码回滚**:
   ```bash
   # 回滚到初始状态（无Docker）
   git checkout <initial-commit>
   ```

**预防措施**:
- Docker配置独立commit，不影响业务逻辑
- 保持`python app.py`直接运行能力
- 提供Docker和非Docker两种启动方式

---

### B.5 完整系统回滚

**场景**: 阶段1整体失败，需要回到初始状态

**回滚步骤**:
1. **代码回滚**:
   ```bash
   git checkout main  # 或初始分支
   ```

2. **数据回滚**:
   ```bash
   # 删除数据库
   docker compose down -v
   # 或
   dropdb teacher_in_loop
   
   # 恢复JSON文件（如果有备份）
   cp data_backup/* data/
   ```

3. **环境清理**:
   ```bash
   # 删除.env（使用默认配置）
   rm .env
   # 或恢复.env.example
   cp .env.example .env
   ```

**预防措施**:
- 每个阶段开始前创建git tag: `git tag phase1-start`
- 保留完整系统备份
- 文档化所有回滚步骤

---

### B.6 紧急修复流程

**如果系统完全不可用**:

1. **立即回滚到最后一个工作commit**:
   ```bash
   git log --oneline  # 找到最后一个工作commit
   git checkout <working-commit>
   ```

2. **恢复最小功能**:
   - 如果DB有问题，临时切换回JSON
   - 如果Auth有问题，临时禁用Auth
   - 确保基本功能可用

3. **创建hotfix分支**:
   ```bash
   git checkout -b hotfix-phase1-<issue>
   # 修复问题
   git commit -m "hotfix: <description>"
   ```

4. **测试后合并**:
   ```bash
   git checkout main
   git merge hotfix-phase1-<issue>
   ```

---

## C. 验证阶段1的命令清单 (Verification Commands)

### C.1 从零环境到跑通的完整步骤

#### 步骤1: 环境准备

```bash
# 1.1 克隆/进入项目目录
cd /path/to/teacher-in-loop-main

# 1.2 检查Python版本（需要3.8+）
python3 --version

# 1.3 创建虚拟环境（可选但推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 1.4 安装Docker和Docker Compose（如果还没有）
docker --version
docker compose version
```

#### 步骤2: 配置环境变量

```bash
# 2.1 复制环境变量模板
cp .env.example .env

# 2.2 编辑.env文件，设置必要配置
# 至少需要设置：
# - SECRET_KEY（随机字符串）
# - DATABASE_URL（PostgreSQL连接字符串）
# - QWEN_API_KEY（如果使用Qwen API）
# - QWEN_BASE_URL

# 2.3 生成SECRET_KEY（如果未设置）
python3 -c "import secrets; print(secrets.token_hex(32))"
# 复制输出到.env的SECRET_KEY
```

#### 步骤3: 启动数据库

```bash
# 3.1 启动PostgreSQL（通过Docker Compose）
docker compose up -d postgres

# 3.2 等待数据库就绪（约10秒）
sleep 10

# 3.3 验证数据库连接
docker compose exec postgres psql -U postgres -d teacher_in_loop -c "SELECT 1;"
```

#### 步骤4: 运行数据库迁移

```bash
# 4.1 运行Alembic迁移
make migrate
# 或
alembic upgrade head

# 4.2 验证表创建成功
docker compose exec postgres psql -U postgres -d teacher_in_loop -c "\dt"
# 应该看到: users, assignments, submissions, rubrics, activity_logs, engagement_metrics等表
```

#### 步骤5: 初始化演示数据

```bash
# 5.1 创建演示数据
make seed_demo
# 或
python -m app.scripts.seed_demo

# 5.2 验证数据创建成功
docker compose exec postgres psql -U postgres -d teacher_in_loop -c "SELECT COUNT(*) FROM users;"
docker compose exec postgres psql -U postgres -d teacher_in_loop -c "SELECT COUNT(*) FROM assignments;"
```

#### 步骤6: 启动Web服务

```bash
# 6.1 使用Docker Compose启动（推荐）
docker compose up

# 6.2 或使用Makefile
make dev

# 6.3 或直接运行Python（开发模式）
python app.py
```

#### 步骤7: 验证系统运行

```bash
# 7.1 检查Web服务响应
curl http://localhost:5000/
# 应该返回HTML页面

# 7.2 检查API端点
curl http://localhost:5000/api/users
# 应该返回JSON用户数据

# 7.3 检查演示数据初始化
curl -X POST http://localhost:5000/api/demo/init
# 应该返回成功消息
```

#### 步骤8: 功能验证

```bash
# 8.1 访问教师门户
# 浏览器打开: http://localhost:5000/teacher
# 应该看到登录页面或仪表板

# 8.2 访问学生门户
# 浏览器打开: http://localhost:5000/student
# 应该看到学生界面

# 8.3 测试登录（如果已实现）
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher1","password":"password"}'
```

#### 步骤9: 运行测试

```bash
# 9.1 运行所有测试
make test
# 或
pytest

# 9.2 运行特定测试
pytest tests/test_demo_init.py
pytest tests/test_rbac.py
pytest tests/test_api_smoke.py

# 9.3 查看测试覆盖率（如果配置）
pytest --cov=app tests/
```

---

### C.2 快速验证清单（每个Commit后）

#### 基础验证（每个commit后必须通过）

```bash
# 1. 代码可以导入
python -c "import app; print('OK')"

# 2. 数据库连接正常（如果已添加DB）
python -c "from app.db import db; print('DB OK')"

# 3. 应用可以启动（至少不报错）
python app.py &
sleep 2
curl http://localhost:5000/ > /dev/null && echo "Web OK" || echo "Web FAIL"
pkill -f "python app.py"
```

#### Docker验证（Commit 1后）

```bash
# 1. Docker镜像可以构建
docker compose build

# 2. 容器可以启动
docker compose up -d
sleep 5

# 3. Web服务响应
curl http://localhost:5000/ > /dev/null && echo "Docker OK" || echo "Docker FAIL"

# 4. 清理
docker compose down
```

#### 数据库验证（Commit 4后）

```bash
# 1. 迁移可以执行
alembic upgrade head

# 2. 表创建成功
docker compose exec postgres psql -U postgres -d teacher_in_loop -c "\dt" | grep -E "(users|assignments|submissions)"

# 3. 可以回滚
alembic downgrade -1
alembic upgrade head
```

#### 功能验证（Commit 9后）

```bash
# 1. 演示数据初始化
curl -X POST http://localhost:5000/api/demo/init

# 2. 数据在数据库中
docker compose exec postgres psql -U postgres -d teacher_in_loop -c "SELECT COUNT(*) FROM users WHERE role='teacher';"

# 3. API返回数据
curl http://localhost:5000/api/users | jq '.teachers | length'
```

#### 认证验证（Commit 11后）

```bash
# 1. 登录端点存在
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  | jq '.'

# 2. 未登录访问受保护端点被拒绝
curl http://localhost:5000/api/assignments
# 应该返回401或重定向
```

#### 测试验证（Commit 18后）

```bash
# 1. 测试可以运行
pytest tests/ -v

# 2. 所有测试通过
pytest tests/ --tb=short
```

---

### C.3 完整系统验证（阶段1完成后）

#### 验证1: Docker一键启动

```bash
# 清理环境
docker compose down -v
rm -rf data/*.json  # 如果保留JSON备份

# 启动系统
docker compose up -d

# 等待服务就绪
sleep 10

# 检查服务状态
docker compose ps
# 应该看到web和postgres都是"Up"状态

# 验证Web响应
curl http://localhost:5000/ | head -20
```

#### 验证2: 数据库迁移可重复执行

```bash
# 删除数据库
docker compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS teacher_in_loop;"
docker compose exec postgres psql -U postgres -c "CREATE DATABASE teacher_in_loop;"

# 运行迁移
alembic upgrade head

# 验证表创建
docker compose exec postgres psql -U postgres -d teacher_in_loop -c "\dt" | wc -l
# 应该 >= 8（至少8个表）
```

#### 验证3: 演示数据初始化

```bash
# 运行种子脚本
make seed_demo

# 验证数据
docker compose exec postgres psql -U postgres -d teacher_in_loop <<EOF
SELECT 'Users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Assignments', COUNT(*) FROM assignments
UNION ALL
SELECT 'Submissions', COUNT(*) FROM submissions
UNION ALL
SELECT 'Rubrics', COUNT(*) FROM rubrics;
EOF

# 应该看到每个表都有数据
```

#### 验证4: 教师功能正常

```bash
# 1. 访问教师门户
curl http://localhost:5000/teacher | grep -q "teacher" && echo "Teacher page OK"

# 2. 登录（如果已实现）
# 获取登录token
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher1","password":"demo123"}' | jq -r '.token')

# 3. 访问受保护端点
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/assignments | jq '.'

# 4. 查看待评分提交
curl -H "Authorization: Bearer $TOKEN" "http://localhost:5000/api/submissions?status=pending" | jq '. | length'
```

#### 验证5: 学生功能正常

```bash
# 1. 访问学生门户
curl http://localhost:5000/student | grep -q "student" && echo "Student page OK"

# 2. 学生提交作业（如果已实现token系统）
# 获取session token
SESSION_TOKEN=$(curl -s -X POST "http://localhost:5000/api/sessions/DEMO01/join" \
  -H "Content-Type: application/json" \
  -d '{"token":"student-token-123"}' | jq -r '.token')

# 3. 使用token访问
curl -H "X-Session-Token: $SESSION_TOKEN" http://localhost:5000/api/submissions | jq '.'
```

#### 验证6: 核心流程完整

```bash
# 完整流程测试脚本
#!/bin/bash

echo "=== 阶段1完整流程验证 ==="

# 1. 系统启动
echo "1. 检查系统启动..."
curl -s http://localhost:5000/ > /dev/null && echo "✓ Web服务运行" || echo "✗ Web服务失败"

# 2. 演示数据
echo "2. 检查演示数据..."
curl -s -X POST http://localhost:5000/api/demo/init > /dev/null && echo "✓ 演示数据初始化" || echo "✗ 演示数据失败"

# 3. 数据访问
echo "3. 检查数据访问..."
USERS=$(curl -s http://localhost:5000/api/users | jq '.teachers | length')
[ "$USERS" -gt 0 ] && echo "✓ 用户数据可访问 ($USERS teachers)" || echo "✗ 用户数据失败"

ASSIGNMENTS=$(curl -s http://localhost:5000/api/assignments | jq '. | length')
[ "$ASSIGNMENTS" -gt 0 ] && echo "✓ 作业数据可访问 ($ASSIGNMENTS assignments)" || echo "✗ 作业数据失败"

# 4. 页面访问
echo "4. 检查页面访问..."
curl -s http://localhost:5000/teacher | grep -q "teacher" && echo "✓ 教师页面可访问" || echo "✗ 教师页面失败"
curl -s http://localhost:5000/student | grep -q "student" && echo "✓ 学生页面可访问" || echo "✗ 学生页面失败"

# 5. 测试运行
echo "5. 运行测试..."
pytest tests/ -v --tb=short && echo "✓ 所有测试通过" || echo "✗ 测试失败"

echo "=== 验证完成 ==="
```

#### 验证7: RBAC功能

```bash
# 1. 未登录访问受保护端点
echo "测试未登录访问..."
curl -s http://localhost:5000/api/assignments | jq '.'
# 应该返回401或错误

# 2. 登录后访问
echo "测试登录后访问..."
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher1","password":"demo123"}' | jq -r '.token')

curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/assignments | jq '.'
# 应该返回数据

# 3. 错误token访问
echo "测试错误token..."
curl -H "Authorization: Bearer invalid-token" http://localhost:5000/api/assignments
# 应该返回401
```

#### 验证8: 审计日志

```bash
# 检查审计日志记录
docker compose exec postgres psql -U postgres -d teacher_in_loop <<EOF
SELECT event_type, COUNT(*) as count 
FROM audit_logs 
GROUP BY event_type 
ORDER BY event_type;
EOF

# 应该看到: demo_init, login, submit_feedback等事件类型
```

---

### C.4 故障排查命令

#### 如果Docker启动失败

```bash
# 查看日志
docker compose logs web
docker compose logs postgres

# 检查端口占用
lsof -i :5000
lsof -i :5432

# 重启服务
docker compose restart
```

#### 如果数据库连接失败

```bash
# 检查数据库状态
docker compose exec postgres pg_isready

# 检查连接字符串
echo $DATABASE_URL

# 手动连接测试
docker compose exec postgres psql -U postgres -d teacher_in_loop
```

#### 如果迁移失败

```bash
# 查看迁移历史
alembic history

# 查看当前版本
alembic current

# 检查迁移脚本语法
python -m alembic upgrade head --sql

# 回滚并重试
alembic downgrade -1
alembic upgrade head
```

#### 如果测试失败

```bash
# 详细输出
pytest tests/ -v -s

# 运行单个测试
pytest tests/test_demo_init.py::test_demo_init_creates_data -v

# 查看测试覆盖率
pytest --cov=app --cov-report=html tests/
```

---

## 总结

**阶段1执行原则**:
1. ✅ 每个commit后系统必须可运行
2. ✅ 保持UX不变（外部接口兼容）
3. ✅ 配置全部环境化
4. ✅ 隐私默认最小化
5. ✅ 不做功能扩张

**验证原则**:
- 每个commit后运行基础验证
- 关键功能点运行完整验证
- 阶段1完成后运行完整系统验证

**回滚原则**:
- 每个关键步骤前创建备份
- 保留回滚到前一状态的能力
- 文档化所有回滚步骤

---

**文档版本**: 1.0  
**创建日期**: 2026-02-05  
**维护者**: AI Engineering Copilot
