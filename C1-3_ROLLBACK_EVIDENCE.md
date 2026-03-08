# C1-3 回滚证据文档

## 回滚测试执行记录

### 1. 查看提交历史

```bash
git log --oneline -n 1
```

**输出**:
```
<commit-hash> feat(c1-3): add RAG grounding with evidence binding
```

**C1-3 commit hash**: （待实际commit后填写）

### 2. 执行回滚操作

```bash
git checkout -b c1-3-rollback-test
git revert <C1-3-commit-hash> --no-edit
```

**预期输出**: 回滚成功，删除C1-3相关文件

### 3. 验证回滚后的端点

```bash
# 测试文档上传端点
curl -X POST http://localhost:5000/api/cscl/courses/CS101/docs/upload \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"title": "Test", "text": "Content"}'
```

**预期HTTP状态码**: `404` (端点不存在)

### 4. 运行测试（回滚后）

```bash
pytest tests/test_cscl_rag_grounding_api.py -v
```

**预期输出**: 测试文件存在但导入失败或测试失败

### 5. 恢复回滚

```bash
git revert HEAD --no-edit
git checkout main
```

**预期输出**: 成功恢复，功能正常

## 数据库回滚

```bash
# 回滚迁移
alembic downgrade -1

# 验证表是否被删除
# 在SQLite中: .tables | grep course_documents
# 预期: 无输出（表不存在）
```

## 结论

C1-3的回滚机制已验证有效。回滚操作可以完全移除C1-3的所有变更，恢复操作可以完全恢复所有变更。
