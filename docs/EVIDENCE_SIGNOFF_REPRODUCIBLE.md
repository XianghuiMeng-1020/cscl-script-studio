# 可复制证据（生产签收用）

## A. 开关行为实测（两次“实跑”）

说明：两次均在容器内通过同一套 pipeline 调用实跑（与 HTTP 调用等价：同一 `run_pipeline` 路径）。  
若需严格“HTTP 实跑”，需在宿主机能访问 `BASE_URL` 且完成登录后，对 `POST /api/cscl/scripts/<script_id>/pipeline/run` 发请求；响应体与下述一致。

### A1. PIPELINE_REQUIRE_CRITIC_SUCCESS=true，且 critic 失败

- **环境**：`PIPELINE_REQUIRE_CRITIC_SUCCESS=true`，`FORCE_CRITIC_FAIL=1`（测试钩子使 critic 直接返回 failed）。
- **要求**：critic 非 success 时 pipeline 提前结束，overall=partial_failed，且不执行 refiner。

**完整响应关键字段：**

```json
{
  "run_id": "run_96b2588654e044d9",
  "status": "partial_failed",
  "stages": [
    { "stage_name": "planner", "status": "success" },
    { "stage_name": "material_generator", "status": "success" },
    { "stage_name": "critic", "status": "failed" }
  ]
}
```

- stages 仅 3 条，无 refiner；status=partial_failed。符合要求。

---

### A2. PIPELINE_REQUIRE_CRITIC_SUCCESS=false，且 critic 失败

- **环境**：`PIPELINE_REQUIRE_CRITIC_SUCCESS=false`，`FORCE_CRITIC_FAIL=1`。
- **要求**：critic 非 success 时 pipeline 仍继续到 refiner；overall 按 refiner 结果判定。

**完整响应关键字段：**

```json
{
  "run_id": "run_dc85c5c2b7de4e88",
  "status": "success",
  "stages": [
    { "stage_name": "planner", "status": "success" },
    { "stage_name": "material_generator", "status": "success" },
    { "stage_name": "critic", "status": "failed" },
    { "stage_name": "refiner", "status": "success" }
  ]
}
```

- 4 条 stages，含 refiner；critic=failed 但 overall=success（由 refiner 决定）。符合要求。

---

### 两次运行后的日志 grep

**命令：**

```bash
docker compose logs web --since=10m 2>&1 | grep -E "run_id|PIPELINE_STAGE_JSON|partial_failed|critic|refiner"
```

**说明**：上述两次实跑在 `docker compose exec web python3` 内执行，JSON 行输出在该 exec 会话的 stdout；gunicorn 主进程未处理该请求，故 `docker compose logs web` 可能无对应行。  
若通过 **HTTP** 触发同一次 pipeline（同一 payload），则处理在 web 进程内完成，`PIPELINE_STAGE_JSON` 会经 logger 写入，可用同一 grep 在 `docker compose logs web` 中检索到。

---

## B. 5×4 回归表原始来源（机器可核对）

### 20 条 stage 原始 JSON（字段：run_id, stage_name, status, provider, model, error）

每行一条 JSON（由汇总命令中的 Python 输出，可管道入 jq 校验）：

```json
{"run_id": "run_1bc80431cda1489c", "stage_name": "planner", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_1bc80431cda1489c", "stage_name": "material_generator", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_1bc80431cda1489c", "stage_name": "critic", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_1bc80431cda1489c", "stage_name": "refiner", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_fe7b62d8b2134ed1", "stage_name": "planner", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_fe7b62d8b2134ed1", "stage_name": "material_generator", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_fe7b62d8b2134ed1", "stage_name": "critic", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_fe7b62d8b2134ed1", "stage_name": "refiner", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_34800fc0f2234087", "stage_name": "planner", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_34800fc0f2234087", "stage_name": "material_generator", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_34800fc0f2234087", "stage_name": "critic", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_34800fc0f2234087", "stage_name": "refiner", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_cdf9e375ec4449e2", "stage_name": "planner", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_cdf9e375ec4449e2", "stage_name": "material_generator", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_cdf9e375ec4449e2", "stage_name": "critic", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_cdf9e375ec4449e2", "stage_name": "refiner", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_990d29955aa34aac", "stage_name": "planner", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_990d29955aa34aac", "stage_name": "material_generator", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_990d29955aa34aac", "stage_name": "critic", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
{"run_id": "run_990d29955aa34aac", "stage_name": "refiner", "status": "success", "provider": "openai", "model": "gpt-4o-mini", "error": null}
```

### 汇总命令与表格输出

**命令（在项目根目录执行，依赖已启动的 web 容器与 T001 脚本）：**

```bash
docker compose --env-file .env exec -T web python3 - <<'PY'
import os, json, sys
sys.path.insert(0, "/app")
os.environ.pop("FORCE_CRITIC_FAIL", None)
from app import create_app
from app.models import CSCLScript
from app.services.cscl_pipeline_service import CSCLPipelineService
spec = {"course_context":{"subject":"DS","topic":"ML","class_size":30,"mode":"sync","duration":90,"description":"x"},"learning_objectives":{"knowledge":["K"],"skills":["S"]},"task_requirements":{"task_type":"structured_debate","expected_output":"o","collaboration_form":"group","requirements_text":"x"}}
app = create_app()
with app.app_context():
    script = CSCLScript.query.filter_by(created_by="T001").first()
    if not script: sys.exit(1)
    for i in range(5):
        r = CSCLPipelineService().run_pipeline(script.id, spec, "T001", {})
        for s in r.get("stages", []):
            row = {"run_id": r.get("run_id"), "stage_name": s.get("stage_name"), "status": s.get("status"), "provider": s.get("provider"), "model": s.get("model"), "error": s.get("error")}
            print(json.dumps(row, ensure_ascii=False))
    # 表格（同上 20 行，此处用 jq 从上面管道解析亦可）
PY
```

**表格（run_id | stage_name | status | provider | model | error）：**

| run_id | stage_name | status | provider | model | error |
|--------|------------|--------|----------|-------|-------|
| run_1bc80431cd | planner | success | openai | gpt-4o-mini | None |
| run_1bc80431cd | material_generator | success | openai | gpt-4o-mini | None |
| run_1bc80431cd | critic | success | openai | gpt-4o-mini | None |
| run_1bc80431cd | refiner | success | openai | gpt-4o-mini | None |
| run_fe7b62d8b2 | planner | success | openai | gpt-4o-mini | None |
| run_fe7b62d8b2 | material_generator | success | openai | gpt-4o-mini | None |
| run_fe7b62d8b2 | critic | success | openai | gpt-4o-mini | None |
| run_fe7b62d8b2 | refiner | success | openai | gpt-4o-mini | None |
| run_34800fc0f2 | planner | success | openai | gpt-4o-mini | None |
| run_34800fc0f2 | material_generator | success | openai | gpt-4o-mini | None |
| run_34800fc0f2 | critic | success | openai | gpt-4o-mini | None |
| run_34800fc0f2 | refiner | success | openai | gpt-4o-mini | None |
| run_cdf9e375ec | planner | success | openai | gpt-4o-mini | None |
| run_cdf9e375ec | material_generator | success | openai | gpt-4o-mini | None |
| run_cdf9e375ec | critic | success | openai | gpt-4o-mini | None |
| run_cdf9e375ec | refiner | success | openai | gpt-4o-mini | None |
| run_990d29955a | planner | success | openai | gpt-4o-mini | None |
| run_990d29955a | material_generator | success | openai | gpt-4o-mini | None |
| run_990d29955a | critic | success | openai | gpt-4o-mini | None |
| run_990d29955a | refiner | success | openai | gpt-4o-mini | None |

---

## C. 日志可观测性验收

### 1. 触发 1 次 pipeline 后的日志原文（≥8 行，覆盖 4 stages）

以下为 `docker compose exec web python3` 内跑一次 pipeline 时，stdout 上的 **PIPELINE_STAGE_JSON** 行（与 logger 输出的格式一致，logger 为 `PIPELINE_STAGE_JSON <json>`）：

```
{"run_id": "run_1bc80431cda1489c", "stage_name": "planner", "provider": "openai", "model": "gpt-4o-mini", "latency_ms": 3503, "success": true, "error_type": null}
{"run_id": "run_1bc80431cda1489c", "stage_name": "material_generator", "provider": "openai", "model": "gpt-4o-mini", "latency_ms": 9923, "success": true, "error_type": null}
{"run_id": "run_1bc80431cda1489c", "stage_name": "critic", "provider": "openai", "model": "gpt-4o-mini", "latency_ms": 10172, "success": true, "error_type": null}
{"run_id": "run_1bc80431cda1489c", "stage_name": "refiner", "provider": "openai", "model": "gpt-4o-mini", "latency_ms": 4361, "success": true, "error_type": null}
```

（同一 run 的 4 条；若再跑一次会得到新 run_id 的 4 条，合计 ≥8 行。）

### 2. Grep 命令与实际用法

**命令：**

```bash
docker compose logs web --since=10m 2>&1 | grep PIPELINE_STAGE_JSON
```

**说明**：  
- 当 pipeline 由 **HTTP 请求** 在 web（gunicorn）进程内执行时，`log_stage_stdout` 会同时写 stdout 和 `_log.info("PIPELINE_STAGE_JSON %s", line)`，gunicorn 通常将 logger 输出到 stderr，`docker compose logs web` 会收到，上述 grep 可检索。  
- 当 pipeline 在 **exec 内** 直接调用时，JSON 行在 exec 会话的 stdout，不在 `docker compose logs web` 中；此时可直接对 exec 输出做 grep，或通过 HTTP 再触发一次后在 logs 中 grep。

### 3. stdout/logger 两路在 gunicorn 下的可见性

- **Logger 路**：`app/services/pipeline/log_observability.py` 中 `_log.info("PIPELINE_STAGE_JSON %s", line)`；gunicorn 默认将 Flask 应用 logger 打到 stderr，容器合并后 `docker compose logs web` 可见。  
- **Stdout 路**：同一文件中 `sys.stdout.write(line + "\n")`；若 gunicorn 未重定向 worker stdout，则也可在 logs 中看到。  
- **稳定性**：重启 web 后，只要再次通过 **HTTP** 触发 pipeline，logger 路会再次输出，grep 可复现。建议验收步骤：`docker compose restart web` → 等待就绪 → 用 HTTP 触发一次 pipeline → 再执行上述 grep。

---

## D. 代码差异锁定

以下为实际命令输出（用于最终 sign-off）：

```text
git rev-parse --short HEAD
a938aa8

git diff --name-only HEAD~1..HEAD
.env.example
app/config.py
app/routes/api.py
app/routes/cscl.py
app/services/cscl_llm_provider.py
app/services/cscl_pipeline_service.py
docker-compose.yml
tests/test_s2_18_provider_selection.py

grep -n "PIPELINE_REQUIRE_CRITIC_SUCCESS" app/config.py app/services/cscl_pipeline_service.py
app/config.py:79:    PIPELINE_REQUIRE_CRITIC_SUCCESS = os.getenv('PIPELINE_REQUIRE_CRITIC_SUCCESS', 'true').lower() == 'true'
app/services/cscl_pipeline_service.py:453:                require_critic_success = Config.PIPELINE_REQUIRE_CRITIC_SUCCESS
app/services/cscl_pipeline_service.py:455:                require_critic_success = os.getenv('PIPELINE_REQUIRE_CRITIC_SUCCESS', 'true').lower() == 'true'
app/services/cscl_pipeline_service.py:458:                pipeline_run.error_message = f"Critic failed (PIPELINE_REQUIRE_CRITIC_SUCCESS=true): {critic_result.get('error')}"

grep -n "PIPELINE_STAGE_JSON\|log_stage_stdout" -R app/services/pipeline
app/services/pipeline/refiner.py:6:from app.services.pipeline.log_observability import log_stage_stdout
app/services/pipeline/refiner.py:47:...
app/services/pipeline/refiner.py:95:...
app/services/pipeline/refiner.py:100:...
app/services/pipeline/planner.py:6:...
app/services/pipeline/planner.py:76:...
app/services/pipeline/planner.py:115:...
app/services/pipeline/material_generator.py:6:...
app/services/pipeline/material_generator.py:47:...
app/services/pipeline/material_generator.py:95:...
app/services/pipeline/material_generator.py:100:...
app/services/pipeline/log_observability.py:11:def log_stage_stdout(
app/services/pipeline/log_observability.py:37:        _log.info("PIPELINE_STAGE_JSON %s", line)
app/services/pipeline/critic.py:7:...
app/services/pipeline/critic.py:41:...
app/services/pipeline/critic.py:63:...
app/services/pipeline/critic.py:128:...
app/services/pipeline/critic.py:133:...
```

---

满足 A+B+C+D 后，可给出「生产可上线」签收。  
当前状态记录为：接近完成，待证据闭环。
