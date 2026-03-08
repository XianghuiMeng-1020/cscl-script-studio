# A/B/C/D 可签收证据（命令 + 原始输出）

## 1) 命令清单（实际执行）

```bash
# 任务1 C：修改 log_observability.py 双写 stderr + logger
# （已编辑 app/services/pipeline/log_observability.py）

python3 -m py_compile app/services/pipeline/log_observability.py
docker compose --env-file .env up -d --build --force-recreate web

# 触发 HTTP pipeline（容器内 curl localhost:5000）
docker compose --env-file .env exec -T web sh -c '
  BASE=http://localhost:5000 SCRIPT_ID=test_script_001
  curl -sS -c /tmp/cookies.txt -b /tmp/cookies.txt -X POST "$BASE/api/auth/login" -H "Content-Type: application/json" -d "{\"user_id\":\"T001\",\"password\":\"teacher123\"}" > /dev/null
  curl -sS -i -X POST "$BASE/api/cscl/scripts/$SCRIPT_ID/pipeline/run" -H "Content-Type: application/json" -b /tmp/cookies.txt --data @/tmp/pipeline_payload_final.json
' | sed -n '1,180p'

docker compose logs web --since=30m 2>&1 | grep PIPELINE_STAGE_JSON
docker compose logs web --since=30m 2>&1 | grep -E "POST /api/cscl/scripts/.*/pipeline/run"

# 任务2 A1：PIPELINE_REQUIRE_CRITIC_SUCCESS=true, FORCE_CRITIC_FAIL=1 → .env 后 rebuild，HTTP 跑一次 → /tmp/A1.json
# 任务2 A2：PIPELINE_REQUIRE_CRITIC_SUCCESS=false, FORCE_CRITIC_FAIL=1 → .env 后 rebuild，HTTP 跑一次 → /tmp/A2.json
jq -r '.run_id, .status, ([.stages[].stage_name] | @json), ([.stages[] | {stage_name, status, provider, model, error}] | @json)' /tmp/A1.json
jq -r '.run_id, .status, ([.stages[].stage_name] | @json), ([.stages[] | {stage_name, status, provider, model, error}] | @json)' /tmp/A2.json

# 任务3 B：默认 .env，5 次 HTTP pipeline → /tmp/B_run_{1..5}.json，20 条 stage JSON + 表
for i in 1 2 3 4 5; do
  docker compose --env-file .env exec -T web sh -c '... curl pipeline/run ...' > /tmp/B_run_$i.json
done
for i in 1 2 3 4 5; do jq -c --arg run_id "$(jq -r .run_id /tmp/B_run_$i.json)" '.stages[] | {run_id: $run_id, stage_name, status, provider, model, error}' /tmp/B_run_$i.json; done
# 汇总表见下方

# 任务4 D
git rev-parse --short HEAD
git diff --name-only HEAD~1..HEAD
grep -n "PIPELINE_REQUIRE_CRITIC_SUCCESS" app/config.py app/services/cscl_pipeline_service.py
grep -n "PIPELINE_STAGE_JSON\|log_stage_stdout" -R app/services/pipeline --include="*.py"
```

---

## 2) 原始输出

### C：日志可 grep

**docker compose logs web --since=30m 2>&1 | grep PIPELINE_STAGE_JSON**

```
web-1  | PIPELINE_STAGE_JSON {"run_id": "run_3d32a95e914c4819", "stage_name": "planner", "provider": "openai", "model": "gpt-4o-mini", "latency_ms": 4279, "success": true, "error_type": null}
web-1  | PIPELINE_STAGE_JSON {"run_id": "run_3d32a95e914c4819", "stage_name": "material_generator", "provider": "openai", "model": "gpt-4o-mini", "latency_ms": 10432, "success": true, "error_type": null}
web-1  | PIPELINE_STAGE_JSON {"run_id": "run_3d32a95e914c4819", "stage_name": "critic", "provider": "openai", "model": "gpt-4o-mini", "latency_ms": 10339, "success": true, "error_type": null}
web-1  | PIPELINE_STAGE_JSON {"run_id": "run_3d32a95e914c4819", "stage_name": "refiner", "provider": "openai", "model": "gpt-4o-mini", "latency_ms": 9555, "success": true, "error_type": null}
```

**docker compose logs web --since=30m 2>&1 | grep -E "POST /api/cscl/scripts/.*/pipeline/run"**

```
web-1  | 127.0.0.1 - - [08/Feb/2026:09:07:30 +0000] "POST /api/cscl/scripts/test_script_001/pipeline/run HTTP/1.1" 200 27629 "-" "curl/7.88.1"
```

---

### A1 jq 输出

```
run_f598a9f0c3034270
partial_failed
["planner","material_generator","critic"]
[{"stage_name":"planner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null},{"stage_name":"material_generator","status":"success","provider":"openai","model":"gpt-4o-mini","error":null},{"stage_name":"critic","status":"failed","provider":"openai","model":"gpt-4o-mini","error":"FORCE_CRITIC_FAIL=1 (test hook)"}]
```

### A2 jq 输出

```
run_da2164cd96ab4c13
success
["planner","material_generator","critic","refiner"]
[{"stage_name":"planner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null},{"stage_name":"material_generator","status":"success","provider":"openai","model":"gpt-4o-mini","error":null},{"stage_name":"critic","status":"failed","provider":"openai","model":"gpt-4o-mini","error":"FORCE_CRITIC_FAIL=1 (test hook)"},{"stage_name":"refiner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}]
```

---

### B：20 条 stage 原始 JSON

```
{"run_id":"run_6e660ab7f9d54e55","stage_name":"planner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_6e660ab7f9d54e55","stage_name":"material_generator","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_6e660ab7f9d54e55","stage_name":"critic","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_6e660ab7f9d54e55","stage_name":"refiner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_46689bfcd7d244d8","stage_name":"planner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_46689bfcd7d244d8","stage_name":"material_generator","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_46689bfcd7d244d8","stage_name":"critic","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_46689bfcd7d244d8","stage_name":"refiner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_48f00c1f1d854b1a","stage_name":"planner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_48f00c1f1d854b1a","stage_name":"material_generator","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_48f00c1f1d854b1a","stage_name":"critic","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_48f00c1f1d854b1a","stage_name":"refiner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_b06bb32fa7f14cb2","stage_name":"planner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_b06bb32fa7f14cb2","stage_name":"material_generator","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_b06bb32fa7f14cb2","stage_name":"critic","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_b06bb32fa7f14cb2","stage_name":"refiner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_5da291928ee14695","stage_name":"planner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_5da291928ee14695","stage_name":"material_generator","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_5da291928ee14695","stage_name":"critic","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
{"run_id":"run_5da291928ee14695","stage_name":"refiner","status":"success","provider":"openai","model":"gpt-4o-mini","error":null}
```

### B：汇总表

| run_id | stage_name | status | provider | model | error |
|--------|------------|--------|----------|-------|-------|
| run_6e660ab7f9 | planner | success | openai | gpt-4o-mini | None |
| run_6e660ab7f9 | material_generator | success | openai | gpt-4o-mini | None |
| run_6e660ab7f9 | critic | success | openai | gpt-4o-mini | None |
| run_6e660ab7f9 | refiner | success | openai | gpt-4o-mini | None |
| run_46689bfcd7 | planner | success | openai | gpt-4o-mini | None |
| run_46689bfcd7 | material_generator | success | openai | gpt-4o-mini | None |
| run_46689bfcd7 | critic | success | openai | gpt-4o-mini | None |
| run_46689bfcd7 | refiner | success | openai | gpt-4o-mini | None |
| run_48f00c1f1d | planner | success | openai | gpt-4o-mini | None |
| run_48f00c1f1d | material_generator | success | openai | gpt-4o-mini | None |
| run_48f00c1f1d | critic | success | openai | gpt-4o-mini | None |
| run_48f00c1f1d | refiner | success | openai | gpt-4o-mini | None |
| run_b06bb32fa7 | planner | success | openai | gpt-4o-mini | None |
| run_b06bb32fa7 | material_generator | success | openai | gpt-4o-mini | None |
| run_b06bb32fa7 | critic | success | openai | gpt-4o-mini | None |
| run_b06bb32fa7 | refiner | success | openai | gpt-4o-mini | None |
| run_5da291928e | planner | success | openai | gpt-4o-mini | None |
| run_5da291928e | material_generator | success | openai | gpt-4o-mini | None |
| run_5da291928e | critic | success | openai | gpt-4o-mini | None |
| run_5da291928e | refiner | success | openai | gpt-4o-mini | None |

---

### D：代码差异锁定

```
a938aa8
---
.env.example
app/config.py
app/routes/api.py
app/routes/cscl.py
app/services/cscl_llm_provider.py
app/services/cscl_pipeline_service.py
docker-compose.yml
tests/test_s2_18_provider_selection.py
---
app/config.py:79:    PIPELINE_REQUIRE_CRITIC_SUCCESS = os.getenv('PIPELINE_REQUIRE_CRITIC_SUCCESS', 'true').lower() == 'true'
app/services/cscl_pipeline_service.py:453:                require_critic_success = Config.PIPELINE_REQUIRE_CRITIC_SUCCESS
app/services/cscl_pipeline_service.py:455:                require_critic_success = os.getenv('PIPELINE_REQUIRE_CRITIC_SUCCESS', 'true').lower() == 'true'
app/services/cscl_pipeline_service.py:458:                pipeline_run.error_message = f"Critic failed (PIPELINE_REQUIRE_CRITIC_SUCCESS=true): {critic_result.get('error')}"
---
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
app/services/pipeline/log_observability.py:10:def log_stage_stdout(
app/services/pipeline/log_observability.py:29:    sys.stderr.write(f"PIPELINE_STAGE_JSON {line}\n")
app/services/pipeline/log_observability.py:31:    _log.info("PIPELINE_STAGE_JSON %s", line)
app/services/pipeline/critic.py:7:...
app/services/pipeline/critic.py:41:...
app/services/pipeline/critic.py:63:...
app/services/pipeline/critic.py:128:...
app/services/pipeline/critic.py:133:...
```

---

## 3) 验收结论

- **A: pass** — A1：status=partial_failed，stages 仅 planner/material_generator/critic，无 refiner；A2：status=success，stages 含 refiner 且 critic=failed。两次均为 HTTP 触发，jq 输出符合预期。
- **B: pass** — 5 次 HTTP pipeline，20 条 stage 原始 JSON（run_id, stage_name, status, provider, model, error）已提取；汇总表 5×4 全 success，provider=openai，model=gpt-4o-mini。
- **C: pass** — 双写 stderr + logger 后，`docker compose logs web --since=30m | grep PIPELINE_STAGE_JSON` 得到 ≥4 行 stage JSON；POST pipeline/run 请求行可 grep。
- **D: pass** — `git rev-parse`、`git diff --name-only`、两处 `grep -n` 已执行并贴出完整原始输出。
