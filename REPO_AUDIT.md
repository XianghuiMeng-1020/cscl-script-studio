# 仓库审计报告 (Repository Audit Report)

**生成日期**: 2026-02-05  
**审计范围**: teacher-in-loop-main 仓库  
**目标**: 将现有"教学反馈支持系统"转换为"GenAI支持的多模态CSCL脚本生成系统"

---

## 1. 仓库结构概览

### 1.1 文件夹树

```
teacher-in-loop-main/
├── app.py                    # Flask主应用（单文件，1077行）
├── requirements.txt          # Python依赖（4个包）
├── README.md                 # 项目说明
├── USER_GUIDE_EN.md          # 用户指南
├── data/                     # JSON数据存储目录
│   ├── users.json            # 用户数据（教师+学生）
│   ├── assignments.json      # 作业数据
│   ├── submissions.json      # 学生提交
│   ├── rubrics.json          # 评分标准
│   ├── feedbacks.json        # 反馈数据（空）
│   ├── activity_logs.json    # 活动日志
│   ├── engagement_metrics.json # 参与度指标
│   └── system_config.json     # 系统配置
├── static/
│   ├── css/
│   │   ├── style.css         # 基础样式
│   │   ├── teacher.css       # 教师门户样式
│   │   ├── student.css       # 学生门户样式
│   │   └── admin.css         # 管理员样式
│   └── js/
│       ├── main.js           # 主JS（未使用）
│       ├── teacher.js        # 教师门户逻辑（989行）
│       ├── student.js        # 学生门户逻辑（500行）
│       └── admin.js          # 管理员逻辑（未检查）
└── templates/
    ├── index.html            # 首页（角色选择）
    ├── teacher.html          # 教师仪表板
    ├── student.html          # 学生门户
    └── admin.html            # 管理员仪表板（未使用）
```

### 1.2 技术栈

- **后端**: Flask 3.0.0 (单文件架构)
- **前端**: 原生JavaScript + HTML/CSS
- **数据存储**: JSON文件（无数据库）
- **AI服务**: OpenAI兼容API（Qwen DashScope）
- **CORS**: Flask-CORS启用
- **部署**: 开发模式（`app.run(debug=True)`）

---

## 2. 端点映射 (Endpoint Map)

### 2.1 页面路由

| 路由 | 方法 | 功能 | 模板 |
|------|------|------|------|
| `/` | GET | 首页（角色选择） | `index.html` |
| `/teacher` | GET | 教师仪表板 | `teacher.html` |
| `/student` | GET | 学生门户 | `student.html` |

### 2.2 API端点

#### 作业管理 (Assignments)
- `GET /api/assignments` - 获取所有作业
- `POST /api/assignments` - 创建作业

#### 评分标准 (Rubrics)
- `GET /api/rubrics` - 获取所有评分标准
- `POST /api/rubrics` - 创建评分标准

#### 学生提交 (Submissions)
- `GET /api/submissions` - 获取提交（支持`?status=`, `?assignment_id=`, `?student_id=`过滤）
- `POST /api/submissions` - 创建提交
- `GET /api/submissions/<id>` - 获取特定提交
- `PUT /api/submissions/<id>/feedback` - 更新反馈（教师评分）

#### AI分析端点
- `POST /api/ai/check-alignment` - 检查反馈与评分标准对齐度
- `POST /api/ai/analyze-quality` - 分析反馈质量
- `POST /api/ai/improve-feedback` - AI优化反馈
- `POST /api/ai/generate-summary` - 生成视觉摘要
- `POST /api/ai/generate-script` - 生成视频脚本
- `POST /api/ai/analyze-work` - 分析学生作业结构
- `POST /api/ai/suggest-scores` - AI建议评分
- `POST /api/ai/detailed-analysis` - 详细反馈分析

#### 参与度追踪 (Engagement)
- `POST /api/engagement/track` - 追踪学生参与
- `GET /api/engagement/stats` - 获取参与度统计

#### 日志 (Logging)
- `GET /api/logs` - 获取活动日志（支持`?type=`, `?user_id=`, `?limit=`）
- `GET /api/logs/summary` - 获取日志摘要

#### 配置 (Configuration)
- `GET /api/config` - 获取系统配置
- `PUT /api/config` - 更新系统配置

#### 统计 (Statistics)
- `GET /api/stats/teacher` - 教师统计
- `GET /api/stats/student/<id>` - 学生统计

#### 用户 (Users)
- `GET /api/users` - 获取所有用户

#### 演示数据 (Demo)
- `POST /api/demo/init` - 初始化演示数据

---

## 3. 当前工作流程 (Current Workflows)

### 3.1 教师工作流

1. **访问教师门户** (`/teacher`)
   - 查看仪表板统计（作业数、待评分、已评分、平均分）
   - 查看最近提交

2. **评分流程**
   - 点击"Pending"查看待评分提交
   - 选择提交卡片进入评分页面
   - **左侧面板**: 显示学生作业内容
   - **右侧面板**: 
     - 评分标准选择（多级评分）
     - 反馈文本输入
     - AI工具按钮：
       - "Analyze Work" - 分析作业结构
       - "Suggest Scores" - AI建议评分
       - "Alignment Check" - 检查反馈覆盖度
       - "Detailed Analysis" - 详细分析
       - "Quality Analysis" - 质量分析
       - "AI Optimize" - 优化反馈
   - 提交反馈后生成视觉摘要和视频脚本

3. **评分标准管理**
   - 查看现有评分标准
   - 创建新评分标准（名称、描述、标准项、权重、等级）

### 3.2 学生工作流

1. **访问学生门户** (`/student`)
   - 选择学生身份（下拉菜单）
   - 查看提交统计

2. **提交作业**
   - 选择作业
   - 输入作业内容
   - 提交

3. **查看反馈**
   - 点击已评分提交
   - 查看模态框：
     - 视觉摘要（雷达图、优势、改进点）
     - 评分标准得分
     - 教师书面反馈
     - 视频脚本

### 3.3 演示初始化流程

- 首页自动调用 `/api/demo/init`（JavaScript）
- 或手动调用创建：
  - 1个评分标准（4个标准项）
  - 1个作业
  - 2个示例提交

---

## 4. 数据存储方法 (Current Data Storage)

### 4.1 JSON文件存储

**优点**:
- 简单，无需数据库配置
- 易于查看和调试
- 适合原型开发

**缺点**:
- 无并发控制（文件锁问题）
- 无事务支持
- 无关系完整性
- 无查询优化
- 无迁移机制
- 不适合生产环境

### 4.2 数据文件结构

#### users.json
```json
{
  "teachers": [{"id", "name", "email", "courses"}],
  "students": [{"id", "name", "email", "courses"}]
}
```

#### assignments.json
```json
[{
  "id", "title", "description", "course_id",
  "due_date", "rubric_id", "created_at", "status"
}]
```

#### submissions.json
```json
[{
  "id", "assignment_id", "student_id", "student_name",
  "content", "submitted_at", "status",
  "feedback", "rubric_scores", "visual_summary",
  "video_script", "feedback_quality", "graded_at"
}]
```

#### rubrics.json
```json
[{
  "id", "name", "description", "criteria": [{
    "id", "name", "description", "weight", "levels"
  }], "created_at"
}]
```

#### activity_logs.json
```json
[{
  "id", "timestamp", "type", "user_id", "details"
}]
```

#### engagement_metrics.json
```json
{
  "<student_id>_<submission_id>": {
    "student_id", "submission_id", "first_view",
    "view_count", "visual_summary_views",
    "video_script_views", "time_spent_seconds", "actions"
  }
}
```

#### system_config.json
```json
{
  "features": {
    "alignment_check": true,
    "quality_analysis": true,
    "ai_suggestions": true,
    ...
  },
  "thresholds": {...},
  "limits": {...}
}
```

---

## 5. UX优势分析 (UX Strengths to Preserve)

### 5.1 教师门户优势

✅ **模块化AI工具按钮**
- 清晰的工具按钮布局
- 每个工具独立调用，结果独立显示
- 教师可以选择性使用工具

✅ **双面板布局**
- 左侧：学生作业（只读）
- 右侧：评分和反馈（可编辑）
- 便于对比和参考

✅ **实时AI分析结果展示**
- AI结果在独立面板中显示
- 可以应用建议或忽略
- 不强制覆盖教师输入

✅ **评分标准可视化**
- 多级评分按钮清晰
- 权重显示
- 已选状态高亮

### 5.2 学生门户优势

✅ **视觉反馈摘要**
- 雷达图展示多维度评分
- 优势和改进点列表
- 鼓励性结语

✅ **模态框反馈展示**
- 不离开主页面
- 结构化展示（摘要、评分、反馈、脚本）
- 可复制脚本

### 5.3 演示初始化模式

✅ **一键演示数据生成**
- `/api/demo/init`端点
- 自动创建完整演示场景
- 适合快速测试和演示

---

## 6. 代码质量评估

### 6.1 架构问题

❌ **单文件架构**
- `app.py` 1077行，所有逻辑集中
- 难以维护和测试
- 无模块分离

❌ **硬编码配置**
- API密钥硬编码（第49行）
- 数据目录路径硬编码（第18行）
- 无环境变量支持

❌ **无错误处理**
- AI调用失败无重试机制
- JSON解析失败无优雅降级
- 文件操作无异常处理

### 6.2 安全问题

❌ **无身份验证**
- 所有端点公开访问
- 无RBAC（基于角色的访问控制）
- 无会话管理

❌ **API密钥暴露**
- Qwen API密钥在代码中
- 应使用环境变量

❌ **无输入验证**
- 无请求参数验证
- 无SQL注入防护（虽然用JSON，但未来迁移需注意）

### 6.3 数据问题

❌ **无数据版本控制**
- 无迁移机制
- 无数据备份策略
- 无审计日志结构化存储

❌ **PII处理不当**
- 学生姓名和邮箱存储在JSON中
- 无伪匿名化机制
- 无数据最小化原则

---

## 7. 功能差距分析 (Gaps to Production)

### 7.1 缺失的核心功能

#### CSCL脚本生成相关
- ❌ 无CSCL脚本生成功能
- ❌ 无脚本理论结构（play/scene/role/scriptlet）
- ❌ 无多模态材料管理
- ❌ 无场景时间线
- ❌ 无角色分配机制
- ❌ 无脚本编辑和版本控制

#### 学生协作相关
- ❌ 无小组管理
- ❌ 无角色分配
- ❌ 无场景流程控制
- ❌ 无协作数据捕获（聊天、评论）
- ❌ 无基线条件支持

#### RAG相关
- ❌ 无文档摄取
- ❌ 无向量检索
- ❌ 无来源追溯（provenance）
- ❌ 无检索结果引用

#### 审计和导出
- ❌ 无AI调用完整日志（模板版本、参数、延迟）
- ❌ 无教师编辑差异日志
- ❌ 无结构化导出包
- ❌ 无研究数据导出

### 7.2 生产级要求差距

#### 数据库
- ❌ 无数据库（仅JSON文件）
- ❌ 无迁移工具（Alembic）
- ❌ 无关系完整性
- ❌ 无查询优化

#### 部署
- ❌ 无Docker化
- ❌ 无docker-compose配置
- ❌ 无生产WSGI服务器（gunicorn/uwsgi）
- ❌ 无Nginx配置
- ❌ 无环境变量配置

#### 测试
- ❌ 无单元测试
- ❌ 无集成测试
- ❌ 无RBAC测试
- ❌ 无导出完整性测试

#### 文档
- ❌ 无架构文档
- ❌ 无设计理由文档
- ❌ 无部署文档
- ❌ 无合规文档
- ❌ 无风险登记

---

## 8. 技术债务清单

1. **代码组织**
   - [ ] 拆分`app.py`为模块化结构
   - [ ] 分离业务逻辑和路由
   - [ ] 创建服务层抽象

2. **配置管理**
   - [ ] 移除硬编码配置
   - [ ] 实现环境变量配置
   - [ ] 创建配置验证

3. **错误处理**
   - [ ] 添加全局错误处理
   - [ ] 实现重试机制
   - [ ] 添加优雅降级

4. **安全性**
   - [ ] 实现身份验证
   - [ ] 实现RBAC
   - [ ] 添加输入验证
   - [ ] 移除硬编码密钥

5. **数据层**
   - [ ] 迁移到PostgreSQL
   - [ ] 实现Alembic迁移
   - [ ] 添加数据验证

6. **测试**
   - [ ] 添加单元测试框架
   - [ ] 编写核心功能测试
   - [ ] 添加集成测试

---

## 9. 保留价值评估

### 9.1 高价值保留项

1. **教师门户UI/UX**
   - 双面板布局
   - 模块化AI工具按钮
   - 实时分析结果展示

2. **演示初始化模式**
   - `/api/demo/init`端点模式
   - 一键创建完整场景

3. **前端交互模式**
   - 模态框反馈展示
   - 视觉摘要展示
   - 实时状态更新

### 9.2 需要重构项

1. **后端架构**
   - 从单文件拆分为模块
   - 引入服务层
   - 添加数据访问层

2. **数据存储**
   - 迁移到数据库
   - 实现版本控制
   - 添加审计日志

3. **AI集成**
   - 抽象LLM提供商
   - 添加调用日志
   - 实现重试和缓存

---

## 10. 迁移复杂度评估

### 10.1 低复杂度（可直接复用）

- 前端HTML/CSS结构
- 基本UI组件
- 演示初始化端点模式

### 10.2 中复杂度（需要适配）

- API端点结构（需扩展）
- 前端JavaScript逻辑（需重构）
- AI调用模式（需抽象）

### 10.3 高复杂度（需要重写）

- 数据存储层（JSON → PostgreSQL）
- 身份验证和RBAC（从零实现）
- CSCL脚本生成模块（全新功能）
- RAG模块（全新功能）
- 审计和导出模块（全新功能）

---

## 11. 风险评估

### 11.1 技术风险

- **数据迁移风险**: JSON到PostgreSQL迁移可能丢失数据
- **功能回归风险**: 重构可能破坏现有功能
- **性能风险**: 数据库查询优化需要时间

### 11.2 时间风险

- **低估复杂度**: 新功能开发可能超时
- **测试不足**: 快速开发可能导致bug

### 11.3 合规风险

- **PII处理**: 现有系统未遵循数据最小化
- **审计缺失**: 无完整审计日志

---

## 12. 建议的迁移策略

### 12.1 渐进式迁移

1. **阶段0**: 审计和规划（当前阶段）
2. **阶段1**: 基础重构（DB + Auth）
3. **阶段2**: CSCL脚本模块
4. **阶段3**: 学生协作模块
5. **阶段4**: RAG模块
6. **阶段5**: 硬化和文档

### 12.2 并行开发

- 保持现有系统运行
- 在新分支开发新功能
- 逐步迁移端点
- 最终切换

---

## 13. 结论

现有系统是一个**功能完整的教学反馈支持系统原型**，具有：

✅ **优势**:
- 清晰的UX设计
- 模块化AI工具集成
- 完整的教师-学生工作流

❌ **劣势**:
- 单文件架构
- JSON文件存储
- 无身份验证
- 无生产级特性

**迁移可行性**: ✅ **高**  
**保留价值**: ✅ **高**（UI/UX和工作流模式）  
**重构工作量**: ⚠️ **中等-高**（需要系统性重构）

**建议**: 采用渐进式迁移策略，保留UX优势，重构后端架构，逐步添加新功能。

---

**审计完成日期**: 2026-02-05  
**审计人员**: AI Engineering Copilot  
**下一步**: 创建详细迁移计划
