# C1-4.1 修复笔记

## 失败根因分析

**失败测试**: `test_unauthenticated_create_decision_401`

**根因一句话结论**: 
`script_with_course` fixture使用了`client` fixture并执行了登录操作，虽然测试中创建了新的`app.test_client()`，但Flask的test_client在某些配置下可能共享session存储，导致未认证请求仍然通过认证检查。

**详细分析**:
1. `script_with_course` fixture依赖`client` fixture
2. `client` fixture返回`app.test_client()`
3. 在`script_with_course`中调用`client.post('/api/auth/login', ...)`设置了session cookie
4. 测试中使用`unauthenticated_client = app.test_client()`创建新client，但可能继承了某些session状态

**解决方案**:
- 方案1（推荐）: 在测试中明确清除session，使用`with app.test_client() as client:`并确保session隔离
- 方案2: 修改`script_with_course` fixture，使其不依赖`client`，而是直接在app context中创建script
- 方案3: 使用Flask的`use_cookies=False`选项创建test_client，避免cookie持久化

**选择方案2**: 修改`script_with_course` fixture，使其在app context中直接创建script，不依赖client和登录状态，这样测试可以完全控制认证状态。
