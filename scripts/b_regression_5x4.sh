#!/usr/bin/env bash
# B. 5×4 回归：输出 20 条 stage JSON（run_id, stage_name, status, provider, model, error），可用 jq 管道汇总
set -e
cd "$(dirname "$0")/.."
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
PY
# 汇总表示例（若已安装 jq）：
# ./scripts/b_regression_5x4.sh 2>/dev/null | jq -r '[.run_id[0:14], .stage_name, .status, .provider, .model, (.error // "None")] | @tsv' | column -t -s $'\t'
