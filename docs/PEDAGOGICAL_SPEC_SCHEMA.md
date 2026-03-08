# Pedagogical Specification Schema

## 概述

Pedagogical Specification（教学规范）是系统生成CSCL脚本的结构化输入。它定义了课程上下文、学习目标、任务要求等关键信息。

## Schema结构

### 完整Schema

```json
{
  "course_context": {
    "subject": "string (required)",
    "topic": "string (required)",
    "class_size": "integer (required, > 0)",
    "mode": "string (required, 'sync' | 'async')",
    "duration": "integer (required, > 0, minutes)"
  },
  "learning_objectives": {
    "knowledge": ["string (required, at least 1)"],
    "skills": ["string (required, at least 1)"],
    "disposition": ["string (optional)"]
  },
  "task_requirements": {
    "task_type": "string (required, see valid types below)",
    "expected_output": "string (required)",
    "collaboration_form": "string (required, see valid forms below)"
  },
  "constraints": {
    "tools": ["string (optional)"],
    "timebox": "integer (optional, > 0, minutes)",
    "assessment_constraints": "string (optional)"
  },
  "rubric_preferences": {
    "criteria": ["string (optional)"],
    "weight": {"string": "float (optional)"},
    "emphasis": "string (optional)"
  },
  "diversity_considerations": "string (optional)",
  "accessibility_considerations": "string (optional)"
}
```

## 字段说明

### course_context（必需）

- **subject**: 学科领域，例如 "Data Science", "Learning Sciences", "Humanities"
- **topic**: 具体主题
- **class_size**: 班级人数（正整数）
- **mode**: 教学模式
  - `sync`: 同步
  - `async`: 异步
- **duration**: 活动时长（分钟，正整数）

### learning_objectives（必需）

- **knowledge**: 知识目标列表（至少1个）
- **skills**: 技能目标列表（至少1个）
- **disposition**: 态度/倾向目标列表（可选）

### task_requirements（必需）

- **task_type**: 任务类型，有效值：
  - `debate`: 辩论
  - `collaborative_writing`: 协作写作
  - `peer_review`: 同伴评审
  - `jigsaw`: 拼图法
  - `role_play`: 角色扮演
  - `case_study`: 案例研究
- **expected_output**: 期望输出描述
- **collaboration_form**: 协作形式，有效值：
  - `group`: 小组
  - `pair`: 配对
  - `individual_with_sharing`: 个人+分享
  - `whole_class`: 全班

### constraints（可选）

- **tools**: 可用工具列表
- **timebox**: 时间限制（分钟）
- **assessment_constraints**: 评估相关约束

### rubric_preferences（可选）

- **criteria**: 评估标准列表
- **weight**: 权重映射（标准名 -> 权重值）
- **emphasis**: 重点说明

## 验证规则

1. 所有必需字段必须存在且非空
2. `class_size` 和 `duration` 必须是正整数
3. `mode` 必须是 `sync` 或 `async`
4. `task_type` 必须在有效值列表中
5. `collaboration_form` 必须在有效值列表中
6. `knowledge` 和 `skills` 必须至少各包含1个元素

## 示例

### 示例1：Data Science

```json
{
  "course_context": {
    "subject": "Data Science",
    "topic": "Machine Learning",
    "class_size": 30,
    "mode": "sync",
    "duration": 90
  },
  "learning_objectives": {
    "knowledge": ["Understand ML basics", "Know common algorithms"],
    "skills": ["Apply algorithms", "Evaluate model performance"]
  },
  "task_requirements": {
    "task_type": "debate",
    "expected_output": "argument for/against ML in healthcare",
    "collaboration_form": "group"
  }
}
```

### 示例2：Learning Sciences

```json
{
  "course_context": {
    "subject": "Learning Sciences",
    "topic": "Collaborative Learning",
    "class_size": 25,
    "mode": "async",
    "duration": 120
  },
  "learning_objectives": {
    "knowledge": ["Understand collaboration principles"],
    "skills": ["Facilitate group discussions"],
    "disposition": ["Value diverse perspectives"]
  },
  "task_requirements": {
    "task_type": "collaborative_writing",
    "expected_output": "group essay on collaboration",
    "collaboration_form": "pair"
  },
  "constraints": {
    "tools": ["Google Docs", "Zoom"],
    "timebox": 60
  }
}
```

### 示例3：Humanities

```json
{
  "course_context": {
    "subject": "Humanities",
    "topic": "Literary Analysis",
    "class_size": 20,
    "mode": "sync",
    "duration": 60
  },
  "learning_objectives": {
    "knowledge": ["Understand literary devices"],
    "skills": ["Analyze texts", "Write critiques"]
  },
  "task_requirements": {
    "task_type": "peer_review",
    "expected_output": "peer feedback on analysis",
    "collaboration_form": "pair"
  },
  "rubric_preferences": {
    "criteria": ["Clarity", "Evidence", "Originality"],
    "emphasis": "Focus on evidence quality"
  }
}
```

## API端点

### POST /api/cscl/spec/validate

验证教学规范。

**请求体**: 上述Schema的JSON对象

**响应**:
- **200 OK**: 验证通过
  ```json
  {
    "valid": true,
    "issues": [],
    "normalized_spec": { ... }
  }
  ```
- **400 Bad Request**: 验证失败
  ```json
  {
    "valid": false,
    "issues": ["error message 1", "error message 2"],
    "normalized_spec": null
  }
  ```

## 使用场景

1. **前端表单验证**: 在用户提交前验证输入
2. **API集成**: 在调用生成API前验证规范
3. **数据规范化**: 获取规范化后的spec用于后续处理
