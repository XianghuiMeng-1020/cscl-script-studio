# C1-1 验收报告：Pedagogical Spec Layer

## 1. 修改文件列表

### 新增文件
- `app/schemas/__init__.py` - Schema模块初始化
- `app/schemas/pedagogical_spec.py` - PedagogicalSpec数据模型定义
- `app/services/spec_validator.py` - Spec校验逻辑实现
- `tests/test_cscl_spec_validation.py` - 测试覆盖（8个测试用例）
- `docs/PEDAGOGICAL_SPEC_SCHEMA.md` - Schema文档

### 修改文件
- `app/routes/cscl.py` - 新增 `/api/cscl/spec/validate` 端点

---

## 2. 新增API列表

### POST /api/cscl/spec/validate
- **功能**: 验证教学规范（Pedagogical Specification）
- **认证**: 无需认证（公开端点）
- **请求体**: JSON格式的spec对象
- **响应**:
  - `200 OK`: 验证通过，返回 `{valid: true, issues: [], normalized_spec: {...}}`
  - `400 Bad Request`: 验证失败，返回 `{valid: false, issues: [...], normalized_spec: null}`
  - `500 Internal Server Error`: 服务器错误

---

## 3. 6个curl样例与结果

### 有效spec示例1：Data Science基础spec
```bash
curl -X POST http://localhost:5000/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "course_context": {
      "subject": "Data Science",
      "topic": "Machine Learning",
      "class_size": 30,
      "mode": "sync",
      "duration": 90
    },
    "learning_objectives": {
      "knowledge": ["Understand ML basics"],
      "skills": ["Apply algorithms"]
    },
    "task_requirements": {
      "task_type": "debate",
      "expected_output": "argument",
      "collaboration_form": "group"
    }
  }'
```

**结果**:
```json
{
  "valid": true,
  "issues": [],
  "normalized_spec": {
    "course_context": {
      "subject": "Data Science",
      "topic": "Machine Learning",
      "class_size": 30,
      "mode": "sync",
      "duration": 90
    },
    "learning_objectives": {
      "knowledge": ["Understand ML basics"],
      "skills": ["Apply algorithms"]
    },
    "task_requirements": {
      "task_type": "debate",
      "expected_output": "argument",
      "collaboration_form": "group"
    }
  }
}
```

### 有效spec示例2：Learning Sciences完整spec（含可选字段）
```bash
curl -X POST http://localhost:5000/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
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
      "expected_output": "group essay",
      "collaboration_form": "pair"
    },
    "constraints": {
      "tools": ["Google Docs", "Zoom"],
      "timebox": 60
    },
    "rubric_preferences": {
      "criteria": ["Clarity", "Evidence"],
      "emphasis": "Focus on evidence quality"
    }
  }'
```

**结果**:
```json
{
  "valid": true,
  "issues": [],
  "normalized_spec": {
    "course_context": {...},
    "learning_objectives": {...},
    "task_requirements": {...},
    "constraints": {
      "tools": ["Google Docs", "Zoom"],
      "timebox": 60
    },
    "rubric_preferences": {
      "criteria": ["Clarity", "Evidence"],
      "emphasis": "Focus on evidence quality"
    }
  }
}
```

### 有效spec示例3：Humanities spec
```bash
curl -X POST http://localhost:5000/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
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
      "expected_output": "peer feedback",
      "collaboration_form": "pair"
    }
  }'
```

**结果**:
```json
{
  "valid": true,
  "issues": [],
  "normalized_spec": {...}
}
```

---

### 无效spec示例1：缺失course_context
```bash
curl -X POST http://localhost:5000/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "learning_objectives": {
      "knowledge": ["Understand ML basics"],
      "skills": ["Apply algorithms"]
    },
    "task_requirements": {
      "task_type": "debate",
      "expected_output": "argument",
      "collaboration_form": "group"
    }
  }'
```

**结果**:
```json
{
  "valid": false,
  "issues": [
    "Missing required field: course_context"
  ],
  "normalized_spec": null
}
```

### 无效spec示例2：空字段
```bash
curl -X POST http://localhost:5000/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "course_context": {
      "subject": "",
      "topic": "Machine Learning",
      "class_size": 30,
      "mode": "sync",
      "duration": 90
    },
    "learning_objectives": {
      "knowledge": [],
      "skills": ["Apply algorithms"]
    },
    "task_requirements": {
      "task_type": "debate",
      "expected_output": "argument",
      "collaboration_form": "group"
    }
  }'
```

**结果**:
```json
{
  "valid": false,
  "issues": [
    "course_context.subject is required and cannot be empty",
    "learning_objectives.knowledge must contain at least one objective"
  ],
  "normalized_spec": null
}
```

### 无效spec示例3：无效mode值
```bash
curl -X POST http://localhost:5000/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "course_context": {
      "subject": "Data Science",
      "topic": "Machine Learning",
      "class_size": 30,
      "mode": "invalid_mode",
      "duration": 90
    },
    "learning_objectives": {
      "knowledge": ["Understand ML basics"],
      "skills": ["Apply algorithms"]
    },
    "task_requirements": {
      "task_type": "debate",
      "expected_output": "argument",
      "collaboration_form": "group"
    }
  }'
```

**结果**:
```json
{
  "valid": false,
  "issues": [
    "course_context.mode must be one of: sync, async"
  ],
  "normalized_spec": null
}
```

---

## 4. pytest摘要

**运行命令**:
```bash
pytest tests/test_cscl_spec_validation.py -v
```

**结果**:
```
============================= test session starts ==============================
platform darwin -- Python 3.13.4, pytest-9.0.2, pluggy-1.6.0
collected 8 items

tests/test_cscl_spec_validation.py::test_valid_spec_basic PASSED         [ 12%]
tests/test_cscl_spec_validation.py::test_valid_spec_with_optional_fields PASSED [ 25%]
tests/test_cscl_spec_validation.py::test_invalid_spec_missing_course_context PASSED [ 37%]
tests/test_cscl_spec_validation.py::test_invalid_spec_empty_fields PASSED [ 50%]
tests/test_cscl_spec_validation.py::test_invalid_spec_invalid_mode PASSED [ 62%]
tests/test_cscl_spec_validation.py::test_invalid_spec_invalid_task_type PASSED [ 75%]
tests/test_cscl_spec_validation.py::test_valid_spec_humanities PASSED    [ 87%]
tests/test_cscl_spec_validation.py::test_empty_request_body PASSED       [100%]

============================== 8 passed in 0.27s ===============================
```

**通过数**: 8/8
**失败数**: 0/8

---

## 5. 回滚命令与结果

### 代码回滚
```bash
# 假设commit hash为 <C1-1-commit-hash>
git revert <C1-1-commit-hash>
```

**验证回滚结果**:
```bash
# 1. 检查文件是否被删除
ls app/schemas/pedagogical_spec.py
# 预期: No such file or directory

# 2. 检查端点是否不存在
curl -X POST http://localhost:5000/api/cscl/spec/validate -d '{}'
# 预期: 404 Not Found

# 3. 检查测试是否失败
pytest tests/test_cscl_spec_validation.py
# 预期: 测试文件不存在或测试失败
```

### 数据库回滚
**说明**: C1-1不涉及数据库迁移，无需数据库回滚。

### 配置回滚
**说明**: C1-1不涉及配置变更，无需配置回滚。

---

## 6. 未完成项

**无未完成项**。

所有C1-1任务已完成：
- ✅ Spec模型定义完成
- ✅ 校验逻辑实现完成
- ✅ API端点实现完成
- ✅ 测试覆盖完成（8个测试用例，全部通过）
- ✅ 文档完成

---

## 验收确认

- [x] 合法spec返回 `valid=true`
- [x] 缺关键字段返回 `valid=false` 且 `issues` 可读
- [x] pytest通过（8个测试用例，0失败）
- [x] 不破坏现有功能（向后兼容）
- [x] 代码可回滚（独立commit）
- [x] 文档齐全

**C1-1阶段完成，可以继续C1-2。**
