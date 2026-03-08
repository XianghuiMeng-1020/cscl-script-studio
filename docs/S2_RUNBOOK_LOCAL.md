# S2 本地运行手册

**版本**: S2重构版  
**日期**: 2026-02-05

本文档提供S2重构后的本地运行与测试指南。

---

## 1. 环境要求

### 1.1 Python环境

- **Python**: 3.8+
- **包管理**: pip

### 1.2 依赖安装

```bash
cd /Users/mrealsalvatore/Desktop/teacher-in-loop-main
pip install -r requirements.txt
```

### 1.3 环境变量（可选）

创建`.env`文件（参考`.env.example`）：

```bash
# LLM Provider
LLM_PROVIDER=qwen
QWEN_API_KEY=your_key_here

# Database (可选)
DATABASE_URL=sqlite:///instance/test.db
```

---

## 2. 启动服务

### 2.1 开发模式

```bash
python app.py
```

**默认端口**: `localhost:5001`

### 2.2 验证启动

访问 `http://localhost:5001/api/health`，应返回：

```json
{
  "status": "ok",
  "db_configured": true,
  "db_connected": true,
  ...
}
```

---

## 3. 访问页面

### 3.1 首页

```
http://localhost:5001/
```

**验证点**:
- ✅ 显示"登录为教师"和"登录为学生"双卡片
- ✅ 显示"快速体验 Demo"按钮
- ✅ 首屏无技术术语（Pipeline/RAG/Refiner）

### 3.2 教师端

```
http://localhost:5001/teacher
```

**验证点**:
- ✅ 标题为"教师工作台"
- ✅ 显示4步流程卡片
- ✅ 状态提示"你现在在第 X/4 步"

### 3.3 学生端

```
http://localhost:5001/student
```

**验证点**:
- ✅ 标题为"学生工作台"
- ✅ 显示"本次任务"区域
- ✅ 可折叠区域（评分标准、历史记录、协作建议）

---

## 4. 运行自动化测试

### 4.1 S2验收测试

```bash
cd /Users/mrealsalvatore/Desktop/teacher-in-loop-main
./scripts/s2_verify.sh
```

### 4.2 测试覆盖

1. ✅ 服务可用性
2. ✅ 页面可达性
3. ✅ 首页文案检查
4. ✅ 教师端关键交互
5. ✅ 学生端关键交互
6. ✅ 权限验证
7. ✅ 多语言提取端点
8. ✅ UI认知负荷检查

### 4.3 预期输出

```
==========================================
S2 UX + IA 重构验收测试
==========================================
Base URL: http://localhost:5001

1. 服务可用性检查
-------------------
✓ PASS: GET /api/health == 200

2. 页面可达性检查
-------------------
✓ PASS: GET / == 200
✓ PASS: GET /teacher == 200
✓ PASS: GET /student == 200

...

==========================================
测试摘要
==========================================
通过: 8
失败: 0

所有测试通过！
```

---

## 5. 手动测试流程

### 5.1 教师端流程测试

1. **访问教师端**
   ```
   http://localhost:5001/teacher
   ```

2. **点击"新建活动"**
   - 应跳转到4步流程

3. **测试4步流程**
   - 步骤1: 导入课程大纲（上传或粘贴）
   - 步骤2: 确认教学目标（填写表单）
   - 步骤3: 生成活动流程（运行生成）
   - 步骤4: 审阅并发布（查看结果）

4. **验证技术详情抽屉**
   - 点击"查看技术详情"
   - 应展开统计信息

### 5.2 学生端流程测试

1. **访问学生端**
   ```
   http://localhost:5001/student
   ```

2. **验证空状态**
   - 无活动时应显示清晰的空状态说明

3. **测试折叠区域**
   - 点击"评分标准摘要" → 应展开
   - 点击"历史记录" → 应展开
   - 点击"协作建议" → 应展开

### 5.3 多语言文本提取测试

#### 5.3.1 英文文本测试

创建`test_en.txt`:
```
Introduction to Data Science

This course covers fundamental concepts.
```

**上传测试**:
- 访问教师端 → 步骤1 → 上传文件
- 应成功提取，无乱码

#### 5.3.2 简体中文测试

创建`test_zh_cn.txt`（GBK编码）:
```
数据科学导论

本课程涵盖基础概念。
```

**上传测试**:
- 应成功提取，GBK→UTF-8转换正确

#### 5.3.3 繁體中文测试

创建`test_zh_tw.txt`（Big5编码）:
```
資料科學導論

本課程涵蓋基礎概念。
```

**上传测试**:
- 应成功提取，Big5→UTF-8转换正确

#### 5.3.4 粘贴上传测试

1. 复制任意文本（中/英/繁）
2. 访问教师端 → 步骤1 → 粘贴到文本域
3. 提交
4. 应成功处理，无乱码

---

## 6. 常见问题

### 6.1 端口被占用

**问题**: `Address already in use`

**解决**:
```bash
# 查找占用进程
lsof -i :5001

# 杀死进程
kill -9 <PID>

# 或使用其他端口
export WEB_PORT=5002
python app.py
```

### 6.2 编码错误

**问题**: 上传中文文件出现乱码

**解决**:
1. 确保文件为UTF-8、GBK或Big5编码
2. 使用文本编辑器转换编码
3. 或使用粘贴上传功能

### 6.3 权限错误

**问题**: 访问API返回401/403

**解决**:
- 401: 需要登录（当前为演示模式，可能不需要）
- 403: 角色权限不足（检查用户角色）

---

## 7. 开发调试

### 7.1 启用调试模式

```bash
export DEBUG=true
python app.py
```

### 7.2 查看日志

日志输出到控制台，包含：
- 请求日志
- 错误堆栈
- 数据库查询（如启用）

### 7.3 浏览器开发者工具

- **F12** 打开开发者工具
- **Console**: 查看JS错误
- **Network**: 查看API请求
- **Elements**: 检查DOM结构

---

## 8. 文件结构

```
teacher-in-loop-main/
├── app/
│   ├── services/
│   │   └── document_service.py  # 文本提取服务
│   └── routes/
│       ├── teacher.py           # 教师端路由
│       └── student.py           # 学生端路由
├── templates/
│   ├── index.html              # 首页
│   ├── teacher.html            # 教师端
│   └── student.html            # 学生端
├── static/
│   ├── css/
│   │   ├── style.css           # 全局样式
│   │   ├── teacher.css         # 教师端样式
│   │   └── student.css         # 学生端样式
│   └── js/
│       ├── teacher.js          # 教师端逻辑
│       └── student.js          # 学生端逻辑
├── scripts/
│   └── s2_verify.sh            # S2验收测试
└── docs/
    ├── S2_ACCEPTANCE_REPORT.md
    ├── S2_UX_COPY_MAP.md
    ├── S2_INFORMATION_ARCHITECTURE.md
    ├── S2_MULTILINGUAL_EXTRACTION.md
    ├── S2_DESIGN_TOKENS.md
    └── S2_RUNBOOK_LOCAL.md    # 本文件
```

---

## 9. 更新记录

- 2026-02-05: S2重构版本创建
