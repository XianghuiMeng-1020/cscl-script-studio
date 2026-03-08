# CSCL Script Studio - 信息架构（IA）

**版本**: 1.0.0  
**更新日期**: 2026-02-05

---

## 1. 公共首页（/）

### 1.1 目标
访客立刻理解"上传课程大纲 -> 自动生成协作活动脚本"

### 1.2 模块顺序

#### (1) Hero（主文案 + 主按钮）
- **标题**: Turn Any Syllabus into Structured CSCL Activities
- **副标题**: Pedagogy-aware, evidence-grounded, teacher-steerable script generation
- **主按钮**: Start as Instructor
- **次按钮**: Preview Student Experience

#### (2) 三步流程
```
Define Spec → Generate Script → Publish Activity
```

#### (3) 角色入口
- **Teacher**: 创建和管理脚本项目
- **Student**: 参与协作活动

#### (4) 功能证据卡
- **Pipeline**: 多阶段生成流程
- **RAG**: 课程文档检索增强
- **Decision Log**: 教师决策追踪
- **Quality Report**: 质量评估报告

#### (5) Demo 快速入口
- **按钮**: Quick Demo Syllabus
- **功能**: 一键填充示例 syllabus，可直接运行

---

## 2. Teacher端（/teacher）

### 2.1 导航结构

```
- Dashboard
- Script Projects
- Spec Validation
- Pipeline Runs
- Course Documents (RAG)
- Decision Timeline
- Quality Reports
- Publish & Export
- Settings
```

### 2.2 Teacher首页布局（必须）

#### 第一屏：四卡统计
- **Active Projects**: 活跃脚本项目数
- **Running Pipelines**: 运行中的Pipeline数
- **Ready to Publish**: 可发布的活动数
- **Avg Quality Score**: 平均质量分数

#### 第二屏：今日下一步
- **主CTA**: Create New Script Project
- **次CTA**: Upload Course Syllabus
- **次CTA**: Open Last Pipeline Run

#### 第三屏：最近活动
- **最近3条pipeline**: 状态、时间、脚本ID
- **最近3条决策记录**: 类型、时间、目标
- **风险提醒**: 例如"grounding不足"警告

### 2.3 关键页面

#### Script Projects
- 列表视图：项目卡片（标题、状态、质量分数、最后更新）
- 创建向导：4步流程

#### Pipeline Runs
- 可视化：4阶段进度（Planner / Material / Critic / Refiner）
- 每阶段显示：状态、耗时、输入摘要、输出摘要
- 技术信息：provider/model/spec_hash/config_fingerprint

#### Quality Report
- 六维度固定展示：
  - coverage
  - pedagogical_alignment
  - argumentation_support
  - grounding
  - safety_checks
  - teacher_in_loop
- 每个维度卡：
  - Score (0-100)
  - Status
  - Evidence（来源链接）
  - Action Tip（改进建议）

---

## 3. Student端（/student）

### 3.1 导航结构

```
- My Activities
- Current Session
- Collaboration Notes
- Reflection & Progress
- Help
```

### 3.2 Student首页布局（必须）

#### 第一屏：当前活动
- **活动标题**: 显示当前活动名称
- **阶段**: 当前处于哪个阶段
- **截止时间**: 活动截止时间
- **我的角色**: 如 Facilitator / Challenger
- **下一步动作**: 单个主按钮

#### 第二屏：当前场景任务卡
- **"你现在要做什么"**: 清晰的任务描述
- **示例句框**: 降低开口成本（提供示例对话）
- **同伴协作提示**: 不超过3条

#### 第三屏：学习进度
- **进度可视化**: 当前活动完成度
- **历史活动**: 已完成的协作活动列表

---

## 4. 关键交互流

### 4.1 Teacher 主流程（4步向导）

#### Step 1: 上传 syllabus
- 页面顶部：固定"你在第 1/4 步"
- 中部：单任务操作（文件上传或文本输入）
- 底部：固定"Back / Continue"
- 右侧："为什么要这一步"（简短说明）

#### Step 2: 填写/校验 Pedagogical Spec
- 表单字段：
  - Course
  - Topic
  - Duration
  - Mode (Sync/Async)
  - Class size
  - Learning Objectives
  - Task Type
  - Expected Output
- 实时验证：显示验证结果
- Demo按钮：一键填充示例数据

#### Step 3: 运行 Pipeline
- 显示4阶段进度：
  - Planner（规划）
  - Material（材料生成）
  - Critic（批判性审查）
  - Refiner（精炼）
- 每阶段状态：pending / running / completed / failed
- 错误处理：可执行建议（非技术黑话）

#### Step 4: 审阅 -> Finalize -> Publish
- 脚本预览：完整脚本结构
- Finalize按钮：标记为最终版本
- Publish按钮：发布给学生

### 4.2 Pipeline可视化页面

**显示内容**:
- Stage名称和顺序
- 每阶段状态（图标+文字）
- 耗时（秒）
- 输入摘要（前100字符）
- 输出摘要（前200字符）
- provider/model信息
- spec_hash/config_fingerprint（可复制）

**错误状态**:
- 红色高亮失败阶段
- 错误消息（用户友好）
- 建议操作（如"检查API密钥"）

### 4.3 Quality Report页面（必须可解释）

**六维度卡片布局**:
```
┌─────────────────────────────────┐
│ Coverage          [85/100] ✓    │
│ Evidence: Run #123, Decision #45 │
│ Tip: Add more course documents   │
└─────────────────────────────────┘
```

每个维度：
- **Score**: 大号数字显示（0-100）
- **Status**: 图标+文字（✓ Good / ⚠ Warning / ✗ Poor）
- **Evidence**: 可点击链接到 run / decision / binding
- **Action Tip**: 具体改进建议

---

## 5. 术语统一（全站）

**只能使用以下术语，不允许混用**:
- Script Project（脚本项目）
- Pedagogical Spec（教学规范）
- Pipeline Run（流水线运行）
- Evidence（证据）
- Decision（决策）
- Quality Report（质量报告）
- Publish（发布）

**禁止使用**:
- Feedback（反馈）
- Rubric（评分标准）
- Grading（评分）
- Assignment（作业）
- Submission（提交）

---

## 6. 微文案规范

### 6.1 按钮文案（动词开头）

- ✅ "Validate Spec" → "Check if this spec is complete"
- ✅ "Run Pipeline" → "Generate a draft CSCL activity script"
- ✅ "Publish" → "Make this activity visible to students"
- ✅ "Create Script Project" → "Start a new CSCL script"
- ✅ "Upload Syllabus" → "Add course materials for RAG"

### 6.2 页面标题

- ✅ "Script Projects"（不是"Projects"）
- ✅ "Pipeline Runs"（不是"Runs"）
- ✅ "Quality Reports"（不是"Reports"）

---

## 7. 空状态（Empty State）

每个空列表必须提供：
- **为什么为空**: 简短说明
- **现在可以做什么**: 操作建议
- **一键动作按钮**: 主要操作

**示例**:
```
┌─────────────────────────────┐
│   📋 No Script Projects    │
│                             │
│   You haven't created any   │
│   script projects yet.     │
│                             │
│   [Create New Script]       │
└─────────────────────────────┘
```

---

## 8. 出错状态

### 8.1 错误分层

#### 用户可修复
- **缺字段**: 给定位+修复建议
- **格式问题**: 高亮错误字段+示例

#### 系统可恢复
- **provider unavailable**: 建议改mock或稍后重试
- **API超时**: 显示重试按钮

#### 权限问题
- **401**: 清晰提示登录
- **403**: 清晰提示角色限制

---

## 9. 响应式布局

### 9.1 Desktop First
- 默认桌面布局
- Tablet可用（768px+）
- 关键流程在 1366x768 无折叠灾难

### 9.2 折叠规则
- Sidebar：Desktop固定，Tablet可折叠
- 卡片网格：Desktop 3列，Tablet 2列，Mobile 1列
- 表单：Desktop双列，Tablet单列

---

## 10. 信息密度

### 10.1 Teacher端
- **高信息密度**: Dashboard显示关键指标
- **详细视图**: Pipeline、Quality Report提供完整信息
- **可展开**: 次要信息默认折叠

### 10.2 Student端
- **低信息密度**: 每屏只显示必要信息
- **单任务聚焦**: 当前场景任务突出显示
- **简化操作**: 减少选择，增加引导

---

## 11. 导航深度

- **最大深度**: 3层（Dashboard → Script Project → Pipeline Run）
- **面包屑**: 深度≥2时显示
- **返回按钮**: 每个详情页都有

---

## 12. 搜索与过滤

### 12.1 Script Projects
- 搜索：按标题、主题
- 过滤：按状态（draft/final/published）
- 排序：按创建时间、更新时间、质量分数

### 12.2 Pipeline Runs
- 过滤：按状态、脚本ID
- 排序：按创建时间（最新优先）

---

## 13. 实施检查清单

- [ ] 首页Hero文案已更新
- [ ] 三步流程已展示
- [ ] Teacher导航已重构
- [ ] Student导航已重构
- [ ] 4步向导流程已实现
- [ ] Pipeline可视化已实现
- [ ] Quality Report六维度已展示
- [ ] 术语已统一
- [ ] 空状态已实现
- [ ] 错误处理已分层
- [ ] 响应式布局已测试
