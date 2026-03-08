# 本地运行与验收指南

**版本**: 1.0.0  
**日期**: 2026-02-05

---

## 快速启动（macOS zsh）

### 1. 启动服务

```bash
cd /Users/mrealsalvatore/Desktop/teacher-in-loop-main
docker compose down -v
docker compose up --build -d

# 等待服务启动（约30秒）
echo "Waiting for services to start..."
sleep 30
```

### 2. 初始化Demo数据

```bash
curl -X POST http://localhost:5001/api/demo/init
```

### 3. 健康检查

```bash
curl http://localhost:5001/api/health | jq
```

### 4. 页面检查

```bash
# 检查首页
curl -I http://localhost:5001/ | head -1
# 应返回: HTTP/1.1 200 OK

# 检查Teacher页面
curl -I http://localhost:5001/teacher | head -1
# 应返回: HTTP/1.1 200 OK

# 检查Student页面
curl -I http://localhost:5001/student | head -1
# 应返回: HTTP/1.1 200 OK
```

### 5. API联调测试

```bash
./scripts/test_api.sh
```

---

## 完整验收流程

### Step 1: 访问首页
1. 打开浏览器访问 `http://localhost:5001`
2. 验证Hero区域显示"CSCL Script Studio"
3. 验证三步流程展示
4. 验证角色入口（Instructor / Student）

### Step 2: Quick Demo流程
1. 点击"Quick Demo Syllabus"按钮
2. 应自动跳转到 `/teacher` 页面
3. 验证Spec表单已自动填充Demo数据

### Step 3: Teacher端验证
1. 在Teacher页面，点击"Create New Script Project"
2. 验证4步向导显示
3. Step 1: 上传Syllabus（可跳过，使用文本输入）
4. Step 2: 点击"Fill Demo Data" → 验证表单填充
5. Step 2: 点击"Validate Spec" → 验证显示验证结果
6. Step 3: 点击"Run Pipeline" → 验证4阶段可视化
7. Step 4: 验证脚本预览和操作按钮

### Step 4: Quality Report验证
1. 在Teacher Dashboard，点击"Quality Reports"
2. 选择一个Script Project
3. 验证6维度卡片显示（Coverage / Pedagogical Alignment / Argumentation Support / Grounding / Safety Checks / Teacher in Loop）

### Step 5: Student端验证
1. 访问 `http://localhost:5001/student`
2. 验证Current Activity显示
3. 验证Current Scene Task显示
4. 验证Example Sentences显示
5. 验证Collaboration Tips显示
6. 验证Progress可视化

---

## API测试命令

### 基础测试

```bash
# Health Check
curl http://localhost:5001/api/health

# Demo Init
curl -X POST http://localhost:5001/api/demo/init

# Spec Validation (Public)
curl -X POST http://localhost:5001/api/cscl/spec/validate \
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

### 需要认证的测试（需先登录）

```bash
# 创建Script Project
curl -X POST http://localhost:5001/api/cscl/scripts \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "title": "Test Script",
    "topic": "Algorithmic Fairness",
    "learning_objectives": ["Objective 1"],
    "task_type": "debate",
    "duration_minutes": 90
  }'

# 运行Pipeline（替换<script_id>）
curl -X POST http://localhost:5001/api/cscl/scripts/<script_id>/pipeline/run \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"spec": {...}}'

# 获取Quality Report（替换<script_id>）
curl http://localhost:5001/api/cscl/scripts/<script_id>/quality-report \
  -H "Cookie: session=..."
```

---

## 截图生成

### 方法1: 使用Puppeteer（推荐）

```bash
# 安装依赖
npm install puppeteer

# 运行截图脚本
BASE_URL=http://localhost:5001 node scripts/screenshot.js
```

### 方法2: 手动截图

1. 启动服务后，在浏览器中访问各页面
2. 使用浏览器开发者工具（F12）→ 更多工具 → 截图
3. 保存到 `outputs/ui/` 目录，命名为：
   - `home_cscl.png`
   - `teacher_dashboard_cscl.png`
   - `teacher_pipeline_run_cscl.png`
   - `teacher_quality_report_cscl.png`
   - `student_dashboard_cscl.png`
   - `student_current_session_cscl.png`

---

## 故障排查

### 服务无法启动
```bash
# 检查Docker状态
docker ps

# 查看日志
docker compose logs

# 重启服务
docker compose restart
```

### API返回401/403
- 检查Flask-Login配置
- 确认session cookie设置正确
- 对于公开端点（如spec/validate），检查`SPEC_VALIDATE_PUBLIC`配置

### Pipeline无法运行
- 检查LLM Provider配置
- 查看环境变量设置
- 使用Mock模式进行测试

### 页面样式异常
- 清除浏览器缓存
- 检查CSS文件是否正确加载
- 查看浏览器控制台错误

---

## 验收检查清单

- [ ] 服务成功启动
- [ ] 首页返回200
- [ ] Teacher页面返回200
- [ ] Student页面返回200
- [ ] Health Check返回ok
- [ ] Demo Init成功
- [ ] Spec Validation成功
- [ ] Quick Demo按钮正常工作
- [ ] 4步向导流程完整
- [ ] Pipeline可视化显示
- [ ] Quality Report显示
- [ ] Student端功能正常
- [ ] 6张截图已生成

---

**最后更新**: 2026-02-05
