# CSCL Script Studio - UX文案指南

**版本**: 1.0.0  
**更新日期**: 2026-02-05

---

## 1. 设计原则

### P0. 一眼懂
用户进入任何页面 3 秒内知道"我是谁、我能做什么、下一步是什么"

### P1. 低认知负荷
每页只承载一个主任务 + 最多两个次任务

### P2. 强引导
每个页面都必须有"Primary CTA（主按钮）"和"Next Step（下一步提示）"

### P3. 文案动作化
按钮动词开头，如 "验证规范 / 运行生成 / 发布活动 / 查看证据"

### P4. 不要AI风
禁止蓝紫霓虹、渐变炫光、悬浮发光、过度拟物

### P5. 视觉克制
留白充分，层级清晰，对比适中，不用花哨动画

### P6. 可解释
任何评分/报告都要有"依据来源"

### P7. 角色分离
Teacher 与 Student 的信息密度和入口动作必须不同

### P8. 无说明可上手
不依赖培训文档也能完成核心流程

---

## 2. 按钮文案规范

### 2.1 主按钮（Primary CTA）

**格式**: 动词 + 名词

| 页面 | 主按钮文案 | 说明 |
|------|-----------|------|
| 首页 | Start as Instructor | 开始作为教师 |
| Teacher Dashboard | Create New Script Project | 创建新脚本项目 |
| Script Project | Run Pipeline | 运行生成流水线 |
| Pipeline Run | View Quality Report | 查看质量报告 |
| Quality Report | Publish Activity | 发布活动 |
| Student Dashboard | Join Current Session | 加入当前会话 |

### 2.2 次按钮（Secondary CTA）

**格式**: 动词 + 名词（可选）

| 上下文 | 次按钮文案 | 说明 |
|--------|-----------|------|
| 首页 | Preview Student Experience | 预览学生体验 |
| Dashboard | Upload Course Syllabus | 上传课程大纲 |
| Dashboard | Open Last Pipeline Run | 打开上次运行 |
| Pipeline | View Decision Timeline | 查看决策时间线 |
| Quality Report | Export Script | 导出脚本 |

### 2.3 文本按钮

**格式**: 动词（简短）

- "Edit"
- "Delete"
- "View Details"
- "Retry"
- "Cancel"

---

## 3. 页面标题规范

### 3.1 格式
**页面名称** + **副标题（可选）**

### 3.2 示例

| 页面 | 标题 | 副标题 |
|------|------|--------|
| Teacher Dashboard | Dashboard | Welcome back! Here's your overview |
| Script Projects | Script Projects | Manage your CSCL activity scripts |
| Pipeline Runs | Pipeline Runs | Track generation progress |
| Quality Report | Quality Report | Evidence-grounded quality assessment |
| Student Dashboard | My Activities | Your collaborative learning sessions |

---

## 4. 表单标签规范

### 4.1 格式
**名词** + **（单位/格式）**

### 4.2 示例

| 字段 | 标签 | 占位符 |
|------|------|--------|
| Course | Course Name | e.g., CS101 |
| Topic | Topic | e.g., Algorithmic Fairness |
| Duration | Duration (minutes) | 90 |
| Class Size | Class Size | 30 |
| Learning Objectives | Learning Objectives | One per line |

### 4.3 帮助文本

**格式**: "Why this matters: [简短说明]"

示例：
- "Why this matters: Used for RAG retrieval"
- "Why this matters: Determines script complexity"

---

## 5. 状态文案规范

### 5.1 Pipeline阶段状态

| 状态 | 文案 | 图标 |
|------|------|------|
| Pending | Waiting to start | ⏳ |
| Running | Generating... | 🔄 |
| Completed | Completed | ✓ |
| Failed | Failed | ✗ |

### 5.2 脚本项目状态

| 状态 | 文案 | 说明 |
|------|------|------|
| Draft | Draft | 草稿状态 |
| Final | Ready to Publish | 可发布 |
| Published | Published | 已发布 |

### 5.3 质量分数状态

| 分数范围 | 状态 | 文案 |
|---------|------|------|
| 80-100 | Good | Excellent |
| 60-79 | Warning | Needs Improvement |
| 0-59 | Poor | Critical Issues |

---

## 6. 错误消息规范

### 6.1 格式
**问题** + **原因** + **解决方案**

### 6.2 示例

#### 用户可修复
```
❌ Missing Required Field
The "Topic" field is required to generate a script.
Please enter a topic and try again.
```

#### 系统可恢复
```
⚠️ Provider Unavailable
The AI provider is temporarily unavailable.
Please try again in a few minutes, or use mock mode for testing.
```

#### 权限问题
```
🔒 Access Denied
You don't have permission to view this script.
Please contact your instructor if you believe this is an error.
```

---

## 7. 成功消息规范

### 7.1 格式
**动作** + **结果** + **下一步**

### 7.2 示例

```
✓ Script Project Created
Your script project "Algorithmic Fairness" has been created.
[Run Pipeline] to generate the activity script.
```

```
✓ Pipeline Completed
Your script has been generated successfully.
[View Quality Report] to review the results.
```

---

## 8. 空状态文案规范

### 8.1 格式
**标题** + **说明** + **操作按钮**

### 8.2 示例

#### Script Projects
```
📋 No Script Projects

You haven't created any script projects yet.
Start by creating your first CSCL activity script.

[Create New Script Project]
```

#### Pipeline Runs
```
🔄 No Pipeline Runs

No pipeline runs found for this script project.
Run the pipeline to generate your first script.

[Run Pipeline]
```

---

## 9. 提示文案规范

### 9.1 工具提示（Tooltip）

**格式**: 简短说明（≤20字）

示例：
- "Check if spec is complete"
- "Generate draft script"
- "View evidence sources"

### 9.2 内联提示

**格式**: "💡 Tip: [建议]"

示例：
- "💡 Tip: Upload course syllabus for better grounding"
- "💡 Tip: Review quality report before publishing"

---

## 10. 表格列标题规范

| 列名 | 格式 | 示例 |
|------|------|------|
| 名称 | 名词 | Title |
| 状态 | 名词 | Status |
| 时间 | 名词 + 单位 | Created At |
| 操作 | 动词 | Actions |

---

## 11. 模态框文案规范

### 11.1 确认对话框

**格式**: 
- **标题**: "确认 [动作]？"
- **正文**: "[动作] 的后果说明"
- **按钮**: "[Cancel] [Confirm]"

示例：
```
Delete Script Project?

This will permanently delete "Algorithmic Fairness" and all associated data.
This action cannot be undone.

[Cancel] [Delete]
```

### 11.2 信息对话框

**格式**:
- **标题**: "[主题]"
- **正文**: "[信息]"
- **按钮**: "[Close]"

---

## 12. 加载状态文案

### 12.1 格式
**动作** + "..."

### 12.2 示例

- "Validating spec..."
- "Running pipeline..."
- "Generating script..."
- "Loading quality report..."

---

## 13. 数字格式化

### 13.1 质量分数
- **格式**: `[分数]/100`
- **示例**: `85/100`

### 13.2 时间
- **格式**: `[数字] [单位]`
- **示例**: `2.5 minutes`, `30 seconds`

### 13.3 日期
- **格式**: `YYYY-MM-DD HH:MM`
- **示例**: `2026-02-05 14:30`

---

## 14. 链接文案规范

### 14.1 格式
**动作** + "详情"（可选）

### 14.2 示例

- "View Pipeline Run"
- "View Evidence"
- "View Decision Timeline"
- "View Quality Report"

---

## 15. 标签（Badge）文案

### 15.1 状态标签

| 状态 | 文案 | 颜色 |
|------|------|------|
| Draft | Draft | Gray |
| Final | Ready | Green |
| Published | Published | Blue |
| Failed | Failed | Red |

### 15.2 数量标签

- **格式**: `[数字]`
- **示例**: `3`, `12`

---

## 16. 多语言考虑

### 16.1 英文优先
- 所有文案以英文为主
- 中文作为辅助（如需要）

### 16.2 术语一致性
- 使用统一的术语表
- 避免同义词混用

---

## 17. 可访问性文案

### 17.1 ARIA标签

```html
<button aria-label="Create new script project">
  Create
</button>
```

### 17.2 错误关联

```html
<input aria-describedby="topic-error" />
<span id="topic-error" role="alert">
  Topic is required
</span>
```

---

## 18. 实施检查清单

- [ ] 所有按钮文案已动作化
- [ ] 页面标题已统一格式
- [ ] 错误消息已分层处理
- [ ] 空状态已提供操作建议
- [ ] 加载状态已添加文案
- [ ] 工具提示已添加
- [ ] ARIA标签已覆盖
- [ ] 术语已统一
- [ ] 数字格式化已统一
- [ ] 多语言考虑已纳入
