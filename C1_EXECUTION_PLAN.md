# C1阶段执行计划：论文级核心骨架

## 执行原则
- 每步可验证（提供命令和输出证据）
- 每步可回滚（独立commit）
- 每步可复现（测试覆盖）
- 不破坏现有功能（保持向后兼容）

---

## 任务树与预计Commit

### 【C1-1】Pedagogical Spec Layer（教学规范层）

**目标**：新增结构化输入模型与校验

**任务分解**：
1. 创建 `app/schemas/pedagogical_spec.py` - 定义Spec模型类
2. 创建 `app/services/spec_validator.py` - 实现校验逻辑
3. 新增 `app/routes/cscl.py` - 添加 `/api/cscl/spec/validate` 端点
4. 创建 `tests/test_cscl_spec_validation.py` - 测试覆盖
5. 更新文档

**预计Commit**：
- `feat(c1-1): add pedagogical spec validation layer`
  - 新增文件：`app/schemas/pedagogical_spec.py`
  - 新增文件：`app/services/spec_validator.py`
  - 修改文件：`app/routes/cscl.py` (新增validate端点)
  - 新增文件：`tests/test_cscl_spec_validation.py`
  - 新增文件：`docs/PEDAGOGICAL_SPEC_SCHEMA.md`

**验收标准**：
- ✅ 合法spec返回 `valid=true`
- ✅ 缺关键字段返回 `valid=false` 且 `issues` 可读
- ✅ pytest通过（至少3个测试用例）

**回滚命令**：
```bash
# 代码回滚
git revert <C1-1-commit-hash>
# 验证：系统应回到C1-1之前状态，/api/cscl/spec/validate端点不存在

# 数据库回滚（如有迁移）
alembic downgrade -1
# 验证：检查迁移历史，确认已回滚

# 配置回滚（如需要）
unset USE_DB_STORAGE
export LLM_PROVIDER=mock
# 验证：系统应仍可正常运行
```

**验证命令**：
```bash
# 1. 测试合法spec
curl -X POST http://localhost:5000/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "course_context": {"subject": "Data Science", "topic": "Machine Learning", "class_size": 30, "mode": "sync", "duration": 90},
    "learning_objectives": {"knowledge": ["Understand ML basics"], "skills": ["Apply algorithms"]},
    "task_requirements": {"task_type": "debate", "expected_output": "argument", "collaboration_form": "group"}
  }'

# 2. 测试缺失字段
curl -X POST http://localhost:5000/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{"course_context": {"subject": "DS"}}'

# 3. 运行测试
pytest tests/test_cscl_spec_validation.py -v
```

---

### 【C1-2】Multi-stage Generation Pipeline（多阶段生成流水线）

**目标**：实现明确分阶段服务（Planner → Material Generator → Critic → Refiner）

**任务分解**：
1. 创建 `app/services/pipeline/` 目录结构
2. 实现 `app/services/pipeline/planner.py` - Planner阶段
3. 实现 `app/services/pipeline/material_generator.py` - Material Generator阶段
4. 实现 `app/services/pipeline/critic.py` - Critic/Verifier阶段
5. 实现 `app/services/pipeline/refiner.py` - Refiner阶段
6. 创建 `app/services/pipeline/pipeline_service.py` - 编排服务
7. 新增数据库表 `pipeline_traces`（迁移文件）
8. 新增 `app/routes/cscl.py` - 添加 `/api/cscl/scripts/<id>/generate-pipeline` 端点
9. 创建 `tests/test_cscl_pipeline_quality.py` - 测试覆盖
10. 更新文档

**预计Commit**：
- `feat(c1-2): add multi-stage generation pipeline`
  - 新增文件：`app/services/pipeline/__init__.py`
  - 新增文件：`app/services/pipeline/planner.py`
  - 新增文件：`app/services/pipeline/material_generator.py`
  - 新增文件：`app/services/pipeline/critic.py`
  - 新增文件：`app/services/pipeline/refiner.py`
  - 新增文件：`app/services/pipeline/pipeline_service.py`
  - 新增文件：`migrations/versions/005_add_pipeline_traces.py`
  - 修改文件：`app/models.py` (新增PipelineTrace模型)
  - 修改文件：`app/routes/cscl.py` (新增generate-pipeline端点)
  - 新增文件：`tests/test_cscl_pipeline_quality.py`
  - 新增文件：`docs/PIPELINE_IO_SCHEMA.md`

**验收标准**：
- ✅ 每阶段有明确I/O schema（JSON）
- ✅ pipeline_trace写入数据库（可审计）
- ✅ provider可切换（mock/openai/qwen）
- ✅ 无外部API时mock必须可运行
- ✅ pytest通过（至少5个测试用例）
- ✅ **跨学科复杂任务验证**：至少3个学科样例（Data Science、Learning Sciences、Humanities）全部跑通

**跨学科验证要求**：
每个学科样例必须完整执行：
1. `POST /api/cscl/spec/validate` - 验证spec
2. `POST /api/cscl/scripts` - 创建脚本
3. `POST /api/cscl/scripts/{id}/generate-pipeline` - 生成pipeline
4. `GET /api/cscl/scripts/{id}/quality-report` - 获取质量报告
5. 输出结构必须统一，证明系统支持跨学科复杂任务

**回滚命令**：
```bash
# 代码回滚
git revert <C1-2-commit-hash>
# 验证：系统应回到C1-2之前状态，generate-pipeline端点不存在

# 数据库回滚
alembic downgrade -1
# 验证：pipeline_traces表应被删除

# 配置回滚
export LLM_PROVIDER=mock
# 验证：系统应仍可正常运行
```

**验证命令**：
```bash
# 1. 创建脚本（先）
curl -X POST http://localhost:5000/api/cscl/scripts \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"title": "Test", "topic": "AI Ethics", "task_type": "debate", "duration_minutes": 60}'

# 2. 调用pipeline（使用mock provider）
LLM_PROVIDER=mock curl -X POST http://localhost:5000/api/cscl/scripts/{script_id}/generate-pipeline \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"generation_options": {"use_rag": false}}'

# 3. 验证trace_id返回
# 4. 运行测试
pytest tests/test_cscl_pipeline_quality.py -v
```

---

### 【C1-3】RAG Grounding（课程资料检索与证据绑定）

**目标**：新增RAG最小实现，支持上传/检索，在scriptlet层支持evidence_ref

**任务分解**：
1. 扩展 `app/services/rag_service.py` - 增强检索功能
2. 新增数据库表 `knowledge_chunks`（迁移文件）
3. 修改 `app/models.py` - 新增KnowledgeChunk模型
4. 新增 `app/routes/cscl.py` - 添加 `/api/cscl/knowledge/upload` 端点（teacher/admin）
5. 新增 `app/routes/cscl.py` - 添加 `/api/cscl/knowledge/search` 端点
6. 修改 `app/services/pipeline/pipeline_service.py` - 集成RAG检索
7. 修改 `app/models.py` - CSCLScriptlet添加evidence_ref字段（迁移）
8. 创建 `tests/test_cscl_rag_grounding.py` - 测试覆盖
9. 更新文档

**预计Commit**：
- `feat(c1-3): add RAG grounding with evidence binding`
  - 修改文件：`app/services/rag_service.py` (增强)
  - 新增文件：`migrations/versions/006_add_knowledge_chunks.py`
  - 新增文件：`migrations/versions/007_add_evidence_ref_to_scriptlets.py`
  - 修改文件：`app/models.py` (新增KnowledgeChunk，修改CSCLScriptlet)
  - 修改文件：`app/routes/cscl.py` (新增knowledge端点)
  - 修改文件：`app/services/pipeline/pipeline_service.py` (集成RAG)
  - 新增文件：`tests/test_cscl_rag_grounding.py`
  - 更新文件：`docs/PIPELINE_IO_SCHEMA.md` (添加evidence_ref说明)

**验收标准**：
- ✅ 支持上传课程文本资料
- ✅ chunk + 检索（关键词/BM25简化可接受）
- ✅ 无资料时可回退空chunks，系统继续可生成
- ✅ 有资料时quality_report体现grounding覆盖度
- ✅ scriptlet层支持evidence_ref
- ✅ pytest通过（至少4个测试用例）
- ✅ **证据绑定覆盖率指标**：quality_report必须包含：
  - `evidence_grounding.coverage_ratio` (0.0-1.0)
  - `evidence_grounding.scriptlets_with_evidence` (整数)
  - `evidence_grounding.total_scriptlets` (整数)
  - 这些指标必须可复算，用于论文报告

**回滚命令**：
```bash
# 代码回滚
git revert <C1-3-commit-hash>
# 验证：系统应回到C1-3之前状态，knowledge端点不存在

# 数据库回滚（两步）
alembic downgrade -1  # 回滚evidence_ref字段
alembic downgrade -1  # 回滚knowledge_chunks表
# 验证：检查迁移历史，确认已回滚

# 配置回滚
unset RAG_ENABLED
# 验证：系统应仍可正常运行（RAG功能禁用）
```

**验证命令**：
```bash
# 1. 上传知识资料（teacher）
curl -X POST http://localhost:5000/api/cscl/knowledge/upload \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"course_id": "CS101", "materials": [{"text": "Machine learning is...", "ref": "syllabus.pdf"}]}'

# 2. 搜索知识
curl "http://localhost:5000/api/cscl/knowledge/search?q=machine+learning&course_id=CS101"

# 3. 无资料时生成（应返回空chunks但成功）
curl -X POST http://localhost:5000/api/cscl/scripts/{script_id}/generate-pipeline \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"generation_options": {"use_rag": true}}'

# 4. 运行测试
pytest tests/test_cscl_rag_grounding.py -v
```

---

### 【C1-4】Teacher-in-the-loop Decision Log（教师决策追踪）

**目标**：在已有revision基础上增强字段，支持决策追踪

**任务分解**：
1. 修改 `app/models.py` - CSCLScriptRevision增强字段（迁移）
2. 修改 `app/routes/cscl.py` - 更新revision记录逻辑
3. 新增 `app/routes/cscl.py` - 添加 `/api/cscl/scripts/<id>/decision-log` 端点
4. 创建 `tests/test_cscl_decision_log.py` - 测试覆盖
5. 更新文档

**预计Commit**：
- `feat(c1-4): enhance teacher-in-the-loop decision tracking`
  - 新增文件：`migrations/versions/008_enhance_decision_log.py`
  - 修改文件：`app/models.py` (CSCLScriptRevision增强)
  - 修改文件：`app/routes/cscl.py` (更新revision逻辑，新增decision-log端点)
  - 新增文件：`tests/test_cscl_decision_log.py`
  - 更新文件：`docs/ARCHITECTURE_DECISIONS.md` (添加teacher-in-loop说明)

**验收标准**：
- ✅ create/update/regenerate/finalize都有日志
- ✅ 可按时间线回放
- ✅ ai_suggestion, teacher_action, rationale_tag字段完整
- ✅ pytest通过（至少3个测试用例）

**回滚命令**：
```bash
# 代码回滚
git revert <C1-4-commit-hash>
# 验证：系统应回到C1-4之前状态，decision-log端点不存在

# 数据库回滚
alembic downgrade -1
# 验证：CSCLScriptRevision表应回到原始结构

# 配置回滚
# 无需特殊配置回滚
```

**验证命令**：
```bash
# 1. 创建脚本（记录create决策）
curl -X POST http://localhost:5000/api/cscl/scripts \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"title": "Test", "topic": "AI Ethics", "task_type": "debate"}'

# 2. 查看决策日志
curl "http://localhost:5000/api/cscl/scripts/{script_id}/decision-log" \
  -H "Cookie: session=..."

# 3. 运行测试
pytest tests/test_cscl_decision_log.py -v
```

---

### 【C1-5】质量报告（Quality Report）

**目标**：新增自动质量报告结构（用于论文写作）

**任务分解**：
1. 创建 `app/services/quality_report.py` - 质量报告生成服务
2. 修改 `app/services/pipeline/pipeline_service.py` - 集成质量报告生成
3. 新增 `app/routes/cscl.py` - 添加 `/api/cscl/scripts/<id>/quality-report` 端点
4. 创建 `tests/test_cscl_quality_report.py` - 测试覆盖
5. 更新文档

**预计Commit**：
- `feat(c1-5): add automated quality report generation`
  - 新增文件：`app/services/quality_report.py`
  - 修改文件：`app/services/pipeline/pipeline_service.py` (集成质量报告)
  - 修改文件：`app/routes/cscl.py` (新增quality-report端点)
  - 新增文件：`tests/test_cscl_quality_report.py`
  - 更新文件：`docs/PIPELINE_IO_SCHEMA.md` (添加quality_report结构)

**验收标准**：
- ✅ 质量报告包含所有必需字段（goal_coverage, role_balance, scene_coherence, evidence_grounding, workload_feasibility, risk_flags, overall_recommendation）
- ✅ 可独立调用quality-report端点
- ✅ pytest通过（至少3个测试用例）

**回滚命令**：
```bash
# 代码回滚
git revert <C1-5-commit-hash>
# 验证：系统应回到C1-5之前状态，quality-report端点不存在

# 数据库回滚
# 无需数据库回滚（quality_report不涉及新表）

# 配置回滚
# 无需特殊配置回滚
```

**验证命令**：
```bash
# 1. 生成pipeline（自动生成质量报告）
curl -X POST http://localhost:5000/api/cscl/scripts/{script_id}/generate-pipeline \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"generation_options": {}}'

# 2. 独立获取质量报告
curl "http://localhost:5000/api/cscl/scripts/{script_id}/quality-report" \
  -H "Cookie: session=..."

# 3. 运行测试
pytest tests/test_cscl_quality_report.py -v
```

---

### 【C1-6】Provider抽象与健康检查增强

**目标**：完善Provider抽象，增强health endpoint

**任务分解**：
1. 完善 `app/services/cscl_llm_provider.py` - 确保所有provider实现完整
2. 修改 `app/routes/api.py` - 增强health endpoint（添加rag_enabled, storage_backend等字段）
3. 创建 `tests/test_provider_abstraction.py` - 测试覆盖
4. 更新文档

**预计Commit**：
- `feat(c1-6): enhance provider abstraction and health check`
  - 修改文件：`app/services/cscl_llm_provider.py` (完善实现)
  - 修改文件：`app/routes/api.py` (增强health endpoint)
  - 新增文件：`tests/test_provider_abstraction.py`
  - 更新文件：`docs/ARCHITECTURE_DECISIONS.md` (添加provider设计说明)

**验收标准**：
- ✅ provider缺key -> 可解释报错（非500）
- ✅ health endpoint返回完整字段（status, provider, use_db_storage, auth_mode, rbac_enabled, rag_enabled, storage_backend）
- ✅ pytest通过（至少3个测试用例）

**回滚命令**：
```bash
# 代码回滚
git revert <C1-6-commit-hash>
# 验证：系统应回到C1-6之前状态，health endpoint应回到原始状态

# 数据库回滚
# 无需数据库回滚

# 配置回滚
export LLM_PROVIDER=mock
# 验证：系统应仍可正常运行
```

**验证命令**：
```bash
# 1. 测试provider缺key（应返回可解释错误）
unset QWEN_API_KEY
LLM_PROVIDER=qwen curl -X POST http://localhost:5000/api/cscl/scripts/{script_id}/generate-pipeline \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"generation_options": {}}'

# 2. 检查health endpoint
curl http://localhost:5000/api/health

# 3. 运行测试
pytest tests/test_provider_abstraction.py -v
```

---

### 【C1-7】文档交付

**目标**：完成所有必需文档

**任务分解**：
1. 创建 `docs/ARCHITECTURE_DECISIONS.md`
2. 创建 `docs/PIPELINE_IO_SCHEMA.md`
3. 创建 `docs/EVALUATION_PLAN.md`
4. 创建 `C1_ACCEPTANCE_REPORT.md`

**预计Commit**：
- `docs(c1-7): add comprehensive documentation for C1 phase`
  - 新增文件：`docs/ARCHITECTURE_DECISIONS.md`
  - 新增文件：`docs/PIPELINE_IO_SCHEMA.md`
  - 新增文件：`docs/EVALUATION_PLAN.md`
  - 新增文件：`C1_ACCEPTANCE_REPORT.md`

**验收标准**：
- ✅ 所有文档齐全，可支持论文方法部分撰写
- ✅ 文档包含架构决策、I/O schema、评估计划
- ✅ **一键可复现实验脚本**：提供 `make c1-e2e`（或等效脚本）实现：
  - 环境准备（设置环境变量）
  - 数据库迁移（flask db upgrade）
  - 运行测试套件（pytest）
  - 执行端到端示例（从spec验证到导出）
  - 导出JSON到 `outputs/` 目录
  - 没有这一项不能宣告C1完成

**一键复现脚本要求**：
```bash
# 脚本应支持：
make c1-e2e
# 或
./scripts/c1_e2e.sh

# 脚本应执行：
1. 环境检查与设置
2. 数据库初始化与迁移
3. 运行所有C1测试
4. 执行端到端流程（至少1个完整示例）
5. 导出结果到 outputs/c1_e2e_result.json
6. 输出验证报告
```

**回滚命令**：
```bash
# 代码回滚
git revert <C1-7-commit-hash>
# 验证：文档文件应被删除，但代码功能不受影响

# 数据库回滚
# 无需数据库回滚（文档不涉及数据库）

# 配置回滚
# 无需特殊配置回滚
```

---

## 端到端验收流程

### 1. 环境准备
```bash
# 设置环境变量
export USE_DB_STORAGE=true
export DATABASE_URL=sqlite:///instance/test_c1.db
export LLM_PROVIDER=mock
export SECRET_KEY=test-secret-key

# 运行迁移
flask db upgrade
```

### 2. 端到端测试脚本
```bash
# 1. 创建teacher用户并登录
# 2. 验证spec
curl -X POST http://localhost:5000/api/cscl/spec/validate -d '{...}'

# 3. 创建脚本
curl -X POST http://localhost:5000/api/cscl/scripts -d '{...}'

# 4. 上传知识资料
curl -X POST http://localhost:5000/api/cscl/knowledge/upload -d '{...}'

# 5. 生成pipeline
curl -X POST http://localhost:5000/api/cscl/scripts/{id}/generate-pipeline -d '{...}'

# 6. 查看质量报告
curl http://localhost:5000/api/cscl/scripts/{id}/quality-report

# 7. 查看决策日志
curl http://localhost:5000/api/cscl/scripts/{id}/decision-log

# 8. 导出脚本
curl http://localhost:5000/api/cscl/scripts/{id}/export
```

### 3. 测试套件运行
```bash
# 运行所有C1相关测试
pytest tests/test_cscl_spec_validation.py \
       tests/test_cscl_pipeline_quality.py \
       tests/test_cscl_rag_grounding.py \
       tests/test_cscl_decision_log.py \
       tests/test_cscl_quality_report.py \
       tests/test_provider_abstraction.py -v

# 预期：所有测试通过（0 failed）
```

### 4. 健康检查
```bash
curl http://localhost:5000/api/health | jq
# 预期包含：status, provider, use_db_storage, auth_mode, rbac_enabled, rag_enabled, storage_backend
```

---

## 回滚策略

每个commit都是独立的，可以单独回滚：
```bash
# 回滚到C1-1之前
git revert <C1-1-commit-hash>

# 回滚到C1-2之前
git revert <C1-2-commit-hash>
# ... 以此类推
```

---

## 预计时间线

- C1-1: 2-3小时
- C1-2: 4-5小时（最复杂）
- C1-3: 3-4小时
- C1-4: 2-3小时
- C1-5: 2-3小时
- C1-6: 1-2小时
- C1-7: 1-2小时

**总计**：约15-22小时

---

## 质量门禁检查清单

在宣告C1完成前，必须全部满足：

- [ ] 无阻塞测试失败（0 failed）
- [ ] 至少一个端到端流程可复现
- [ ] 缺失API key不崩溃（可解释错误）
- [ ] 有研究导出schema文档（C1阶段为pipeline trace schema）
- [ ] 文档齐全，可支持论文方法部分撰写
- [ ] health endpoint返回所有必需字段
- [ ] 所有新增API都有测试覆盖

---

## 下一步（C2阶段预览）

C2阶段将实现：
- Enactment Session模型
- Enactment APIs
- Research Export标准化
- 审计日志增强

---

**请确认此计划后，我将开始执行C1-1任务。**
