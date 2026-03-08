# CSCL Script Studio - Demo运行手册

**版本**: 1.0.0  
**更新日期**: 2026-02-05

---

## 1. Quick Demo Syllabus

### 1.1 示例数据

点击首页"Quick Demo Syllabus"按钮，自动填充以下数据：

```json
{
  "course": "Introduction to Data Science",
  "topic": "Algorithmic Fairness in Education",
  "duration_minutes": 90,
  "mode": "Sync",
  "class_size": 30,
  "learning_objectives": [
    "Explain basic fairness metrics",
    "Compare trade-offs between accuracy and fairness",
    "Construct evidence-based group arguments"
  ],
  "task_type": "Structured debate + collaborative synthesis memo",
  "expected_output": [
    "Group argument map",
    "300-word joint reflection"
  ]
}
```

### 1.2 使用流程

1. **访问首页** (`http://127.0.0.1:5000/`)
2. **点击"Quick Demo Syllabus"按钮**
3. **自动填充spec表单**
4. **点击"Validate Spec"** → 应显示验证通过
5. **点击"Run Pipeline"** → 开始生成脚本
6. **查看Pipeline进度** → 4阶段可视化
7. **查看Quality Report** → 六维度质量评估
8. **Preview Script** → 查看生成的脚本结构

---

## 2. API端点验证

### 2.1 健康检查

```bash
curl http://127.0.0.1:5000/api/health
```

**预期响应**:
```json
{
  "status": "ok",
  "db_configured": true,
  "db_connected": true,
  "use_db_storage": true,
  "provider": "openai",
  "auth_mode": "session+token",
  "rbac_enabled": true
}
```

### 2.2 Demo初始化

```bash
curl -X POST http://127.0.0.1:5000/api/demo/init
```

**预期响应**:
```json
{
  "success": true,
  "message": "Demo data initialized"
}
```

---

## 3. CSCL API端点测试

### 3.1 Spec验证（公开访问）

```bash
curl -X POST http://127.0.0.1:5000/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "course": "CS101",
    "topic": "Algorithmic Fairness",
    "duration_minutes": 90,
    "mode": "Sync",
    "class_size": 30,
    "learning_objectives": ["Objective 1"],
    "task_type": "debate"
  }'
```

**预期响应**:
```json
{
  "valid": true,
  "issues": [],
  "normalized_spec": {
    "course": "CS101",
    "topic": "Algorithmic Fairness",
    ...
  }
}
```

### 3.2 创建Script Project（需要认证）

```bash
# 先登录获取token（示例）
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "teacher1",
    "password": "password"
  }'

# 使用token创建脚本
curl -X POST http://127.0.0.1:5000/api/cscl/scripts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "title": "Demo Script",
    "topic": "Algorithmic Fairness",
    "learning_objectives": ["Objective 1"],
    "task_type": "debate",
    "duration_minutes": 90
  }'
```

### 3.3 运行Pipeline（需要认证）

```bash
curl -X POST http://127.0.0.1:5000/api/cscl/scripts/<script_id>/pipeline/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "spec": {
      "course": "CS101",
      "topic": "Algorithmic Fairness",
      "duration_minutes": 90,
      "mode": "Sync",
      "class_size": 30,
      "learning_objectives": ["Objective 1"],
      "task_type": "debate"
    }
  }'
```

**预期响应**:
```json
{
  "success": true,
  "run_id": "run_xxx",
  "status": "completed",
  "stages": [...]
}
```

### 3.4 获取Quality Report（需要认证）

```bash
curl http://127.0.0.1:5000/api/cscl/scripts/<script_id>/quality-report \
  -H "Authorization: Bearer <token>"
```

**预期响应**:
```json
{
  "success": true,
  "report": {
    "coverage": {"score": 85, "status": "good", ...},
    "pedagogical_alignment": {...},
    "argumentation_support": {...},
    "grounding": {...},
    "safety_checks": {...},
    "teacher_in_loop": {...}
  }
}
```

### 3.5 获取Pipeline Run详情（需要认证）

```bash
curl http://127.0.0.1:5000/api/cscl/pipeline/runs/<run_id> \
  -H "Authorization: Bearer <token>"
```

**预期响应**:
```json
{
  "success": true,
  "run": {
    "run_id": "run_xxx",
    "script_id": "script_xxx",
    "status": "completed",
    ...
  },
  "stages": [
    {
      "stage": "planner",
      "status": "completed",
      "duration_seconds": 12.5,
      ...
    },
    ...
  ]
}
```

### 3.6 获取Decision Timeline（需要认证）

```bash
curl http://127.0.0.1:5000/api/cscl/scripts/<script_id>/decision-timeline/export \
  -H "Authorization: Bearer <token>"
```

---

## 4. 权限验证测试

### 4.1 401未认证

```bash
# 不提供token访问受保护端点
curl http://127.0.0.1:5000/api/cscl/scripts
```

**预期响应**:
```json
{
  "error": "Authentication required",
  "code": "AUTH_REQUIRED"
}
```
**状态码**: 401

### 4.2 403权限不足

```bash
# 使用student角色访问teacher-only端点
curl -X POST http://127.0.0.1:5000/api/cscl/scripts \
  -H "Authorization: Bearer <student_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test"}'
```

**预期响应**:
```json
{
  "error": "Insufficient permissions",
  "code": "PERMISSION_DENIED",
  "required_roles": ["teacher", "admin"],
  "user_role": "student"
}
```
**状态码**: 403

### 4.3 200成功访问

```bash
# 使用teacher角色访问
curl http://127.0.0.1:5000/api/cscl/scripts \
  -H "Authorization: Bearer <teacher_token>"
```

**预期响应**: 200 OK with data

---

## 5. 前端功能验证

### 5.1 首页功能

- [ ] Hero区域显示正确
- [ ] "Start as Instructor"按钮可点击
- [ ] "Preview Student Experience"按钮可点击
- [ ] "Quick Demo Syllabus"按钮填充数据
- [ ] 三步流程显示正确
- [ ] 功能证据卡显示正确

### 5.2 Teacher Dashboard

- [ ] 四卡统计显示正确
- [ ] "Create New Script Project"主按钮可点击
- [ ] 最近活动列表显示
- [ ] 侧边栏导航可切换

### 5.3 Script Project创建

- [ ] 4步向导流程正常
- [ ] Step 1上传syllabus正常
- [ ] Step 2填写spec正常
- [ ] Step 3运行Pipeline正常
- [ ] Step 4审阅发布正常

### 5.4 Pipeline可视化

- [ ] 4阶段进度显示
- [ ] 每阶段状态正确
- [ ] 耗时显示正确
- [ ] 输入/输出摘要显示
- [ ] provider/model信息显示

### 5.5 Quality Report

- [ ] 六维度卡片显示
- [ ] 分数显示正确
- [ ] 状态图标正确
- [ ] 证据链接可点击
- [ ] 改进建议显示

### 5.6 Student Dashboard

- [ ] 当前活动信息显示
- [ ] 我的角色显示
- [ ] 下一步动作按钮显示
- [ ] 当前场景任务卡显示
- [ ] 示例句框显示

---

## 6. 错误处理验证

### 6.1 表单验证错误

- [ ] 必填字段缺失显示错误
- [ ] 格式错误显示提示
- [ ] 错误消息可读（非技术黑话）

### 6.2 API错误处理

- [ ] 401错误显示登录提示
- [ ] 403错误显示权限提示
- [ ] 500错误显示友好消息
- [ ] 网络错误显示重试建议

### 6.3 Pipeline错误

- [ ] 阶段失败显示错误
- [ ] 错误消息有可执行建议
- [ ] 可重试失败阶段

---

## 7. 性能验证

### 7.1 加载时间

- [ ] 首页加载<2秒
- [ ] Dashboard加载<1秒
- [ ] Pipeline可视化加载<1秒
- [ ] Quality Report加载<2秒

### 7.2 交互响应

- [ ] 按钮点击响应<100ms
- [ ] 表单提交反馈及时
- [ ] 加载状态清晰

---

## 8. 截图清单

需要生成以下截图（保存到 `outputs/ui/`）：

- [ ] `home_cscl.png` - 首页完整视图
- [ ] `teacher_dashboard_cscl.png` - Teacher Dashboard
- [ ] `teacher_pipeline_run_cscl.png` - Pipeline可视化页面
- [ ] `teacher_quality_report_cscl.png` - Quality Report页面
- [ ] `student_dashboard_cscl.png` - Student Dashboard
- [ ] `student_current_session_cscl.png` - Student当前会话页面

---

## 9. 完整Demo流程

### 9.1 端到端流程

1. **启动服务**
   ```bash
   python app.py
   ```

2. **访问首页**
   - 打开 `http://127.0.0.1:5000/`
   - 验证Hero和功能展示

3. **创建Demo项目**
   - 点击"Quick Demo Syllabus"
   - 验证数据填充
   - 点击"Start as Instructor"

4. **创建Script Project**
   - 填写表单
   - 验证Spec
   - 运行Pipeline

5. **查看结果**
   - 查看Pipeline进度
   - 查看Quality Report
   - 预览Script

6. **发布活动**
   - Finalize Script
   - Publish Activity

7. **Student体验**
   - 切换到Student视图
   - 查看当前活动
   - 参与协作

---

## 10. 问题排查

### 10.1 API不响应

- 检查服务是否运行
- 检查端口是否正确
- 检查CORS配置

### 10.2 认证失败

- 检查token是否有效
- 检查角色权限
- 检查session配置

### 10.3 Pipeline失败

- 检查LLM provider配置
- 检查API密钥
- 查看日志错误信息

---

## 11. 验收标准

### 11.1 功能完整性

- [ ] 所有核心功能可用
- [ ] 所有API端点响应正常
- [ ] 所有页面可访问

### 11.2 用户体验

- [ ] 页面加载流畅
- [ ] 交互响应及时
- [ ] 错误提示友好

### 11.3 可访问性

- [ ] 键盘导航正常
- [ ] 屏幕阅读器支持
- [ ] 对比度满足标准

---

## 12. 参考命令

### 12.1 完整测试脚本

```bash
#!/bin/bash

# Health check
echo "Testing health endpoint..."
curl http://127.0.0.1:5000/api/health

# Demo init
echo "Initializing demo data..."
curl -X POST http://127.0.0.1:5000/api/demo/init

# Spec validation (public)
echo "Testing spec validation..."
curl -X POST http://127.0.0.1:5000/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d @demo_spec.json

echo "Demo test completed!"
```

### 12.2 Demo Spec JSON

保存为 `demo_spec.json`:
```json
{
  "course": "Introduction to Data Science",
  "topic": "Algorithmic Fairness in Education",
  "duration_minutes": 90,
  "mode": "Sync",
  "class_size": 30,
  "learning_objectives": [
    "Explain basic fairness metrics",
    "Compare trade-offs between accuracy and fairness",
    "Construct evidence-based group arguments"
  ],
  "task_type": "Structured debate + collaborative synthesis memo",
  "expected_output": [
    "Group argument map",
    "300-word joint reflection"
  ]
}
```
