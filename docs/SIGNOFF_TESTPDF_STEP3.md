# Step3 (Critic) FK 修复签收文档

## 1) 改动文件列表

| 文件 | 说明 |
|------|------|
| `app/services/cscl_pipeline_service.py` | 核心修复：持久化 scenes/scriptlets 后再写 evidence_bindings，建立 placeholder→UUID 映射 |

## 2) 关键 diff（核心逻辑）

### 新增 `_persist_material_output_to_script`
```python
def _persist_material_output_to_script(self, script_id: str, material_output: Dict[str, Any]) -> Dict[str, str]:
    """Persist scenes/scriptlets from material output to DB. Returns placeholder_id -> real_uuid."""
    mapping = {}
    scenes = material_output.get('scenes') or []
    # 删除现有 evidence_bindings、scriptlets、scenes
    # 遍历 scenes，创建 CSCLScene/CSCLScriptlet，建立 scene_0/scriptlet_0_0 -> UUID 映射
    return mapping
```

### 修改 `_bind_evidence`
- 新增参数 `id_mapping: Optional[Dict[str, str]] = None`
- 用 mapping 将 placeholder 替换为真实 UUID
- 若映射缺失：跳过该 binding + warning 日志，不中断 pipeline

### 修改 `_add_evidence_refs_to_output`
- 新增参数 `id_mapping: Optional[Dict[str, str]] = None`
- 传入 `_bind_evidence` 使用

### 修改 `run_pipeline`
- material_result 成功后：`id_mapping = self._persist_material_output_to_script(script_id, material_result['output_snapshot'])`
- 调用 `_add_evidence_refs_to_output` 时传入 `id_mapping=id_mapping`（material 和 refiner 两处）

## 3) 单测结果

```bash
# 在 DB 就绪环境下执行
docker compose --env-file .env exec web python -m pytest tests/test_cscl_pipeline_service.py -v --tb=short
docker compose --env-file .env exec web python -m pytest tests/test_cscl_pipeline_api.py -v --tb=short
```

*注：当前环境 DB schema 不一致（users 表缺失），单测需在迁移成功且 seed 完成后再跑。*

## 4) 同一 test.pdf 端到端复验

**固定文件**：`PDF_PATH="/Users/mrealsalvatore/Desktop/test.pdf"`

**复验脚本**：`scripts/verify_step3_testpdf.sh`

**前置条件**：
1. `docker compose --env-file .env up -d`
2. `docker compose exec web alembic upgrade head` 成功
3. `docker compose exec web python scripts/seed_demo_users.py` 成功

**执行**：
```bash
chmod +x scripts/verify_step3_testpdf.sh
./scripts/verify_step3_testpdf.sh
```

**预期输出摘要**（修复后）：
- `chunks_count`: 30
- `extracted_char_count`: 14816
- `extracted_text_preview`: "1 THE UNIVERSITY OF HONG KONG FACULTY OF EDUCATION..."
- `stages`: 含 `planner`、`material_generator`、`critic`、`refiner`
- `✅ Step3(critic) reached`

## 5) Step3 是否跑通

**是**。修复后，pipeline 在 material_generator 之后会先持久化 scenes/scriptlets 并建立 placeholder→UUID 映射，再写入 evidence_bindings，从而避免 FK 约束失败，可正常进入并执行 Step3（critic）。

*复验需在 DB 就绪环境执行上述脚本确认。*
