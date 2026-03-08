#!/usr/bin/env bash
# 可复制证据：A 开关实测 / B 5×4 表 / C 日志验收 / D 代码差异
set -e
cd "$(dirname "$0")/.."
BASE="${BASE_URL:-http://127.0.0.1:5001}"
COOKIES="/tmp/evidence_cookies_$$"
SPEC_JSON='{"spec":{"course_context":{"subject":"DS","topic":"ML Ethics","class_size":30,"mode":"sync","duration":90,"description":"Evidence run"},"learning_objectives":{"knowledge":["K1"],"skills":["S1"]},"task_requirements":{"task_type":"structured_debate","expected_output":"map","collaboration_form":"group","requirements_text":"Evidence"}}'

cleanup() { rm -f "$COOKIES"; }
trap cleanup EXIT

# Login and get first script_id
login() {
  curl -sS -c "$COOKIES" -b "$COOKIES" -X POST "$BASE/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"T001","password":"teacher123"}' > /dev/null
}
get_script_id() {
  curl -sS -b "$COOKIES" "$BASE/api/cscl/scripts" | python3 -c "
import sys,json
d=json.load(sys.stdin)
scripts=d.get('scripts',d) if isinstance(d,dict) else d
ids=[s.get('id') for s in (scripts if isinstance(scripts,list) else []) if s.get('id')]
print(ids[0] if ids else '')
" 2>/dev/null || echo ""
}

echo "=== A. 开关行为实测（两次 HTTP）==="
echo ""

# A1: PIPELINE_REQUIRE_CRITIC_SUCCESS=true, FORCE_CRITIC_FAIL=1 → partial_failed, no refiner
echo "--- A1: PIPELINE_REQUIRE_CRITIC_SUCCESS=true, FORCE_CRITIC_FAIL=1 ---"
login
SCRIPT_ID=$(get_script_id)
if [ -z "$SCRIPT_ID" ]; then
  echo "No script_id (list scripts failed or empty). Creating script via API..."
  CREATE=$(curl -sS -b "$COOKIES" -X POST "$BASE/api/cscl/scripts" -H "Content-Type: application/json" \
    -d '{"title":"Evidence script","task_type":"structured_debate","course_context":{},"learning_objectives":{},"task_requirements":{}}')
  SCRIPT_ID=$(echo "$CREATE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('script',d).get('id','') or d.get('id',''))" 2>/dev/null)
fi
if [ -z "$SCRIPT_ID" ]; then
  echo "A1 skip: could not get script_id"
else
  RESP_A1=$(curl -sS -b "$COOKIES" -X POST "$BASE/api/cscl/scripts/$SCRIPT_ID/pipeline/run" \
    -H "Content-Type: application/json" -d "$SPEC_JSON")
  echo "Response (run_id, status, stages count):"
  echo "$RESP_A1" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('run_id:', d.get('run_id'))
print('status:', d.get('status'))
stages=d.get('stages',[])
print('stages count:', len(stages))
for s in stages: print('  -', s.get('stage_name'), s.get('status'))
" 2>/dev/null || echo "$RESP_A1"
fi
echo ""
echo "Logs (run_id | PIPELINE_STAGE_JSON | partial_failed | critic | refiner):"
docker compose --env-file .env logs web --since=10m 2>&1 | grep -E "run_id|PIPELINE_STAGE_JSON|partial_failed|critic|refiner" || true
echo ""

# A2: PIPELINE_REQUIRE_CRITIC_SUCCESS=false, FORCE_CRITIC_FAIL=1 → continue to refiner
echo "--- A2: PIPELINE_REQUIRE_CRITIC_SUCCESS=false, FORCE_CRITIC_FAIL=1 ---"
echo "（需先重启 web 并设置 PIPELINE_REQUIRE_CRITIC_SUCCESS=false FORCE_CRITIC_FAIL=1 后重跑）"
echo ""

echo "=== B. 5×4 回归表（机器可核对）==="
docker compose --env-file .env exec -T web python3 - <<'PYB'
import sys, json
sys.path.insert(0, "/app")
from app import create_app
from app.models import CSCLScript
from app.services.cscl_pipeline_service import CSCLPipelineService
spec = {"course_context":{"subject":"DS","topic":"ML","class_size":30,"mode":"sync","duration":90,"description":"x"},"learning_objectives":{"knowledge":["K"],"skills":["S"]},"task_requirements":{"task_type":"structured_debate","expected_output":"o","collaboration_form":"group","requirements_text":"x"}}
app = create_app()
with app.app_context():
    script = CSCLScript.query.filter_by(created_by="T001").first()
    if not script: print("NO_SCRIPT"); sys.exit(1)
    rows = []
    for i in range(5):
        r = CSCLPipelineService().run_pipeline(script.id, spec, "T001", {})
        for s in r.get("stages", []):
            row = {"run_id": r.get("run_id"), "stage_name": s.get("stage_name"), "status": s.get("status"), "provider": s.get("provider"), "model": s.get("model"), "error": s.get("error")}
            rows.append(row)
            print(json.dumps(row, ensure_ascii=False))
    print("---TABLE---")
    print("run_id|stage_name|status|provider|model|error")
    for row in rows:
        print(row["run_id"][:14], row["stage_name"], row["status"], row["provider"], row["model"], (row["error"] or "")[:30], sep="|")
PYB
echo ""

echo "=== C. 日志可观测性 ==="
echo "触发 1 次 pipeline 后的日志原文（grep PIPELINE_STAGE_JSON）："
docker compose --env-file .env logs web --since=15m 2>&1 | grep "PIPELINE_STAGE_JSON" || echo "(无输出则需先通过 HTTP 触发一次 pipeline)"
echo ""
echo "Grep 命令: docker compose logs web --since=10m 2>&1 | grep PIPELINE_STAGE_JSON"
echo ""

echo "=== D. 代码差异锁定 ==="
git rev-parse --short HEAD
git diff --name-only HEAD~1..HEAD 2>/dev/null || true
grep -n "PIPELINE_REQUIRE_CRITIC_SUCCESS" app/config.py app/services/cscl_pipeline_service.py 2>/dev/null || true
grep -n "PIPELINE_STAGE_JSON\|log_stage_stdout" -R app/services/pipeline 2>/dev/null || true
