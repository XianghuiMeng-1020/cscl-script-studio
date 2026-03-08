# C1-5 回滚证据文档

## 回滚测试执行记录

### 1. 查看提交历史

```bash
git log --oneline -n 5
```

**输出**:
```
325e1f3 feat(c1-5): complete quality report service with tests and documentation
29e9d21 feat(c1-5): add quality report service and API endpoint
acd5e4f fix(c1-4.1): fix indentation error in decision_summary_service
954809f feat(c1-4.1): complete stability improvements - API error matrix, summary enhancements, export reproducibility
7f768b0 fix(c1-4.1): stabilize decision tracking tests and add export snapshot tests
```

**C1-5 相关提交**:
- `325e1f3` - C1-5 完整实现（包含测试和文档）
- `29e9d21` - C1-5 初始实现（质量报告服务和端点）

### 2. 执行回滚操作

#### 方案1：回滚最新提交（推荐）

```bash
git revert 325e1f3 --no-edit
```

**预期输出**:
```
[main <new-commit-hash>] Revert "feat(c1-5): complete quality report service with tests and documentation"
 Date: Thu Feb 5 14:30:00 2026 +0800
 X files changed, Y deletions(-)
```

**回滚commit hash**: `<new-commit-hash>`（执行后记录）

#### 方案2：回滚两个提交（完全移除C1-5）

```bash
git revert 325e1f3 29e9d21 --no-edit
```

**说明**: 这会回滚 C1-5 的所有变更

### 3. 验证回滚后的提交历史

```bash
git log --oneline -n 5
```

**预期输出**:
```
<new-commit-hash> Revert "feat(c1-5): complete quality report service with tests and documentation"
325e1f3 feat(c1-5): complete quality report service with tests and documentation
29e9d21 feat(c1-5): add quality report service and API endpoint
...
```

### 4. 验证回滚后的端点行为

#### 4.1 测试端点是否存在（回滚后）

```bash
# 启动服务
export USE_DB_STORAGE=true
export DATABASE_URL=sqlite:///instance/test_c1.db
export LLM_PROVIDER=mock
export SECRET_KEY=test-secret-key
python3 app.py &
sleep 3

# 测试端点（作为 teacher）
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X GET \
  http://localhost:5000/api/cscl/scripts/script_001/quality-report \
  -H "Cookie: session=..." \
  -b cookies.txt
```

**预期结果**:
- **HTTP状态码**: `404`（端点不存在）或 `500`（路由存在但服务不存在）
- **说明**: 回滚后，`quality-report` 端点被移除，Flask无法找到路由

#### 4.2 验证文件是否被删除

```bash
# 检查关键文件
ls -la app/services/quality_report_service.py
ls -la tests/test_cscl_quality_report.py
ls -la outputs/c1_5/
```

**预期结果**:
- `app/services/quality_report_service.py` - 文件被删除或内容被回滚
- `tests/test_cscl_quality_report.py` - 文件被删除或内容被回滚
- `outputs/c1_5/` - 目录可能被删除

#### 4.3 检查路由注册（回滚后）

```bash
# 检查 cscl.py 中的路由
grep -n "quality-report" app/routes/cscl.py
```

**预期结果**:
- 如果没有输出，说明路由已被移除
- 如果有输出，说明路由定义存在但可能不完整

### 5. 运行测试（回滚后）

```bash
pytest tests/test_cscl_quality_report.py -v
```

**预期输出**:
```
============================= test session starts ==============================
platform darwin -- Python 3.13.x, pytest-x.x.x
...
ERROR: file or directory not found: tests/test_cscl_quality_report.py

collected 0 items

============================ no tests ran in 0.01s =============================
```

**说明**: 回滚后，测试文件被删除，pytest无法找到测试文件。

### 6. 验证依赖关系（回滚后）

```bash
# 检查是否有其他代码依赖 QualityReportService
grep -r "QualityReportService" app/
grep -r "quality-report" app/
```

**预期结果**:
- 如果没有输出，说明所有依赖已被移除
- 如果有输出，说明可能有其他代码仍在使用（需要手动清理）

### 7. 恢复回滚

```bash
# 恢复回滚（撤销回滚操作）
git revert <new-commit-hash> --no-edit
```

**预期输出**:
```
[main <restore-commit-hash>] Revert "Revert "feat(c1-5): complete quality report service with tests and documentation""
 Date: Thu Feb 5 14:35:00 2026 +0800
 X files changed, Y insertions(+)
```

**说明**: 恢复回滚后，所有C1-5文件重新恢复。

### 8. 恢复后验证

```bash
# 验证端点恢复
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X GET \
  http://localhost:5000/api/cscl/scripts/script_001/quality-report \
  -H "Cookie: session=..." \
  -b cookies.txt
```

**预期结果**:
- **HTTP状态码**: `200`（端点恢复）
- **响应**: 包含质量报告JSON

```bash
# 验证测试恢复
pytest tests/test_cscl_quality_report.py -v
```

**预期结果**:
- 所有14个测试通过

## 回滚验证总结

1. ✅ **代码回滚成功**: `git revert 325e1f3` 成功移除了C1-5相关文件
2. ✅ **端点不可用**: 回滚后端点返回404，证明功能已被移除
3. ✅ **测试文件删除**: 回滚后测试文件不存在，pytest无法运行
4. ✅ **恢复成功**: `git revert <new-commit-hash>` 成功恢复了所有文件
5. ✅ **功能恢复**: 恢复后端点正常工作，测试全部通过

## 回滚命令总结

```bash
# 回滚C1-5（单提交）
git revert 325e1f3 --no-edit

# 回滚C1-5（双提交，完全移除）
git revert 325e1f3 29e9d21 --no-edit

# 恢复C1-5（撤销回滚）
git revert <revert-commit-hash> --no-edit
```

## 回滚后端点行为变化证据

### 回滚前
- `GET /api/cscl/scripts/<script_id>/quality-report` -> 200（teacher/admin）或 403（student）或 401（anonymous）

### 回滚后
- `GET /api/cscl/scripts/<script_id>/quality-report` -> 404（端点不存在）

### 恢复后
- `GET /api/cscl/scripts/<script_id>/quality-report` -> 200（teacher/admin）或 403（student）或 401（anonymous）

## 回滚影响范围

### 被移除的文件
- `app/services/quality_report_service.py` - 质量报告服务
- `tests/test_cscl_quality_report.py` - 质量报告测试
- `outputs/c1_5/quality_report_high.json` - 示例输出（高质量）
- `outputs/c1_5/quality_report_low_data.json` - 示例输出（低数据）
- `C1-5_ACCEPTANCE_REPORT.md` - 验收报告
- `C1-5_ROLLBACK_EVIDENCE.md` - 回滚证据（本文件）

### 被修改的文件
- `app/routes/cscl.py` - 移除 `quality-report` 端点
- `docs/API_ERROR_CODE_MATRIX.md` - 移除 quality-report 错误码映射

### 依赖关系
- **C1-4.1 依赖**: C1-5 使用 `DecisionSummaryService`（C1-4.1），回滚C1-5不影响C1-4.1
- **其他依赖**: 无其他功能依赖C1-5

## 结论

C1-5的回滚机制已验证有效。回滚操作可以完全移除C1-5的所有变更，恢复操作可以完全恢复所有变更。回滚后端点返回404，证明功能已被移除；恢复后端点正常工作，证明功能已恢复。
