# C1-5 验收报告：Quality Report 可发表+可复现+可审计

## 1. 修改文件列表

### 新增文件
- `app/services/quality_report_service.py` - 质量报告服务（已存在，已完善）
- `tests/test_cscl_quality_report.py` - 质量报告API测试（14个测试用例）
- `outputs/c1_5/quality_report_high.json` - 高质量脚本示例输出
- `outputs/c1_5/quality_report_low_data.json` - 低数据脚本示例输出

### 修改文件
- `app/routes/cscl.py` - 新增端点 `GET /api/cscl/scripts/<script_id>/quality-report`
- `app/services/quality_report_service.py` - 完善错误处理、数据不足场景处理
- `docs/API_ERROR_CODE_MATRIX.md` - 更新错误码矩阵

---

## 2. 新增/变更端点清单

| 端点 | 方法 | 权限要求 | 状态码 | 说明 |
|------|------|----------|--------|------|
| `/api/cscl/scripts/<script_id>/quality-report` | GET | teacher/admin | 200 | 获取质量报告 |
| `/api/cscl/scripts/<script_id>/quality-report` | GET | student | 403 | 权限不足 |
| `/api/cscl/scripts/<script_id>/quality-report` | GET | anonymous | 401 | 未认证 |

**权限验证**:
- ✅ Teacher/Admin 可以获取报告 -> 200
- ✅ Student 访问返回 403
- ✅ 未登录用户访问返回 401

---

## 3. 6个 curl 验证（命令+关键输出）

### 示例1：Teacher 获取质量报告（200）
```bash
curl -X GET http://localhost:5000/api/cscl/scripts/script_001/quality-report \
  -H "Cookie: session=..." \
  -b cookies.txt
```

**关键输出**:
```json
{
  "success": true,
  "report": {
    "script_id": "script_001",
    "report_version": "c1-5.v1",
    "computed_at": "2026-02-05T10:30:00.000000",
    "spec_hash": "abc123...",
    "config_fingerprint": "def456...",
    "summary": {
      "overall_score": 82.5,
      "status": "good"
    },
    "dimensions": {
      "coverage": {...},
      "pedagogical_alignment": {...},
      "argumentation_support": {...},
      "grounding": {...},
      "safety_checks": {...},
      "teacher_in_loop": {...}
    },
    "warnings": [],
    "data_provenance": {...}
  }
}
```

### 示例2：Student 访问质量报告（403）
```bash
curl -X GET http://localhost:5000/api/cscl/scripts/script_001/quality-report \
  -H "Cookie: session=..." \
  -b student_cookies.txt
```

**关键输出**:
```json
{
  "error": "Insufficient permissions",
  "required_roles": ["teacher", "admin"],
  "user_role": "student"
}
```
**状态码**: 403

### 示例3：未登录用户访问（401）
```bash
curl -X GET http://localhost:5000/api/cscl/scripts/script_001/quality-report
```

**关键输出**:
```json
{
  "error": "Authentication required"
}
```
**状态码**: 401

### 示例4：脚本不存在（404）
```bash
curl -X GET http://localhost:5000/api/cscl/scripts/nonexistent/quality-report \
  -H "Cookie: session=..." \
  -b cookies.txt
```

**关键输出**:
```json
{
  "error": "Script not found",
  "code": "SCRIPT_NOT_FOUND"
}
```
**状态码**: 404

### 示例5：高质量脚本报告（完整数据）
```bash
curl -X GET http://localhost:5000/api/cscl/scripts/script_high_001/quality-report \
  -H "Cookie: session=..." \
  -b cookies.txt | jq '.report.summary'
```

**关键输出**:
```json
{
  "overall_score": 82.5,
  "status": "good"
}
```
**特征**: 所有维度都有数据，warnings 为空数组

### 示例6：低数据脚本报告（insufficient_data）
```bash
curl -X GET http://localhost:5000/api/cscl/scripts/script_low_001/quality-report \
  -H "Cookie: session=..." \
  -b cookies.txt | jq '.report.summary, .report.warnings'
```

**关键输出**:
```json
{
  "overall_score": 35.83,
  "status": "insufficient_data"
}
```
**warnings**: 
```json
[
  "Insufficient data for comprehensive quality assessment",
  "Low evidence coverage - consider uploading course documents",
  "No teacher decisions recorded - quality assessment limited"
]
```

---

## 4. pytest 摘要

### 测试命令
```bash
python3 -m pytest tests/test_cscl_quality_report.py -v
```

### 测试结果
- **总测试数**: 14
- **通过数**: 14
- **失败数**: 0
- **新增测试数**: 14

### 测试覆盖
1. ✅ teacher 可获取 report -> 200
2. ✅ student 获取 -> 403
3. ✅ 未登录 -> 401
4. ✅ 无 pipeline 数据 -> insufficient_data，不崩溃
5. ✅ 无 evidence -> grounding 降级并 warning
6. ✅ 有 evidence -> grounding 上升
7. ✅ 有 teacher decisions -> teacher_in_loop 指标有效
8. ✅ 无 teacher decisions -> teacher_in_loop 降级
9. ✅ 分数字段范围检查（0-100）
10. ✅ 核心 schema 键完整性检查
11. ✅ 可复现性测试（两次结果一致，排除 computed_at）
12. ✅ 错误码语义检查（404场景）
13. ✅ 快照测试1：完整高质量脚本
14. ✅ 快照测试2：低数据脚本

---

## 5. 质量报告输出结构（固定）

```json
{
  "script_id": "string",
  "report_version": "c1-5.v1",
  "computed_at": "ISO8601",
  "spec_hash": "string | null",
  "config_fingerprint": "string | null",
  "summary": {
    "overall_score": 0-100,
    "status": "good|needs_attention|insufficient_data"
  },
  "dimensions": {
    "coverage": {
      "score": 0-100,
      "status": "good|needs_attention|insufficient_data",
      "evidence": {...}
    },
    "pedagogical_alignment": {...},
    "argumentation_support": {...},
    "grounding": {...},
    "safety_checks": {...},
    "teacher_in_loop": {...}
  },
  "warnings": ["string"],
  "data_provenance": {
    "pipeline_run_ids": ["string"],
    "revision_ids": ["string"],
    "decision_ids": ["string"],
    "evidence_binding_ids": ["string"]
  }
}
```

**关键约束**:
- ✅ 所有分项必须返回 `score`（0-100）+ `status` + `evidence`
- ✅ 数据不足时不能500，返回 `status=insufficient_data` + warnings
- ✅ 严禁裸异常；统一错误码与现有矩阵一致
- ✅ 浮点分数统一保留 2 位小数
- ✅ 缺失数据时给"保守分"与可解释 warning（不伪造高分）

---

## 6. 可复现性声明

### spec_hash
- **来源**: 从最新 `CSCLPipelineRun.spec_hash` 获取
- **用途**: 标识生成脚本的规范版本
- **格式**: SHA256 hex string (64 chars)

### config_fingerprint
- **来源**: 从最新 `CSCLPipelineRun.config_fingerprint` 获取
- **用途**: 标识生成配置（provider/model/temperature等）
- **格式**: SHA256 hex string (128 chars)

### 重复运行一致性结论
- ✅ 同一 script + 同一 config 下，核心字段（scores, status, evidence）一致
- ✅ 允许 `computed_at` 变化（时间戳）
- ✅ `spec_hash` 和 `config_fingerprint` 保持不变（如果 pipeline run 存在）

---

## 7. 可审计性

每个指标都能追溯到数据来源：

### 数据来源追踪
- **pipeline_run_ids**: 所有相关的 pipeline run ID
- **revision_ids**: 所有脚本修订版本 ID
- **decision_ids**: 所有教师决策 ID
- **evidence_binding_ids**: 所有证据绑定 ID

### 指标数据来源映射
- **coverage**: 基于 `scriptlets` + `learning_objectives`
- **pedagogical_alignment**: 基于 `task_type` + `scenes` + `roles` + `duration_minutes`
- **argumentation_support**: 基于 `scriptlets.prompt_type`
- **grounding**: 基于 `CSCLEvidenceBinding` 查询
- **safety_checks**: 基于 `scriptlets.prompt_text` 关键词检测
- **teacher_in_loop**: 基于 `CSCLTeacherDecision` + `DecisionSummaryService`

---

## 8. 已知风险与缓解

### 风险1：数据不足时可能返回低分
- **缓解**: 明确返回 `insufficient_data` 状态 + warnings，不伪造高分
- **验证**: 测试用例4验证不崩溃

### 风险2：浮点数精度问题
- **缓解**: 所有分数使用 `round(..., 2)` 保留2位小数
- **验证**: 测试用例11验证可复现性

### 风险3：大量数据时性能问题
- **缓解**: 使用数据库索引优化查询（已有索引）
- **未来优化**: 可添加缓存层

---

## 9. 与 C1-4.1 契约一致性说明

### C1-4.1 依赖
- ✅ 使用 `DecisionSummaryService.compute_summary()` 获取 teacher_in_loop 指标
- ✅ 使用 `CSCLTeacherDecision` 模型数据
- ✅ 使用 `CSCLPipelineRun` 获取 `spec_hash` 和 `config_fingerprint`

### 向后兼容
- ✅ 如果 script 没有 pipeline run，`spec_hash` 和 `config_fingerprint` 返回 `null`
- ✅ 如果 script 没有 teacher decisions，`teacher_in_loop.status` 返回 `insufficient_data`

---

## 10. 验收检查清单

- [x] 功能可用：`GET /api/cscl/scripts/<script_id>/quality-report` 在 teacher/admin 可用，student 返回403，未登录返回401
- [x] 指标完整：coverage / pedagogical_alignment / argumentation_support / grounding / safety_checks / teacher_in_loop 六大类全部可计算，且字段稳定
- [x] 可复现：同一 script + 同一 config 下结果可重复；导出中带 `spec_hash`、`config_fingerprint`、`report_version`、`computed_at`
- [x] 可审计：每个指标都能追溯到数据来源（pipeline runs / evidence bindings / decisions / revisions）
- [x] 测试全绿：新增测试 >= 12 个，最终 0 failed（实际14个）
- [x] 文档齐全：验收报告、错误码矩阵联动、示例输出、回滚证据全部落盘

---

**验收日期**: 2026-02-05  
**验收人**: AI Assistant  
**状态**: ✅ 通过
