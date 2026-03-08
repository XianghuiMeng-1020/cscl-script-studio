# Step3 (Critic) 真实验收签收文档

## 本次 commit hash

```
a938aa8fac4208e4b3ab2d73a3c76b26ae4f61bc
```

## 改动文件列表

| 文件 | 说明 |
|------|------|
| `app/services/cscl_pipeline_service.py` | FK 修复：material 后持久化 scenes/scriptlets，建立 placeholder→UUID 映射，写 evidence_bindings 时替换 |

## A. 环境修复（可复制）

```bash
set -euo pipefail
cd "/Users/mrealsalvatore/Desktop/teacher-in-loop-main"

docker compose --env-file .env down -v 2>/dev/null || true
docker compose --env-file .env up -d --build
docker compose --env-file .env ps

# 数据库迁移（全新 DB 需执行）
docker compose --env-file .env exec -T web alembic upgrade head

# Seed demo 用户
docker compose --env-file .env exec -T web python scripts/seed_demo_users.py

# 健康检查（必须 200）
curl -sSI http://127.0.0.1:5001/api/health | head -5
```

## B. E2E 复验（同一 test.pdf，可复制）

```bash
BASE="http://127.0.0.1:5001"
PDF_PATH="/Users/mrealsalvatore/Desktop/test.pdf"
[ -f "$PDF_PATH" ] || { echo "❌ file missing: $PDF_PATH"; exit 1; }

rm -f cookies.txt

# 1) 登录（user_id + Demo@12345）
LOGIN_RESP=$(curl -sS -X POST "$BASE/api/auth/login" -H "Content-Type: application/json" -c cookies.txt -b cookies.txt \
  --data '{"user_id":"teacher_demo","password":"Demo@12345"}')

# 2) 创建 script
CREATE_RESP=$(curl -sS -X POST "$BASE/api/cscl/scripts" -H "Content-Type: application/json" -c cookies.txt -b cookies.txt \
  --data '{"title":"pdf-step3-final","topic":"Photosynthesis","task_type":"structured_debate","duration_minutes":60}')
SCRIPT_ID=$(echo "$CREATE_RESP" | python3 -c "import json,sys; j=json.load(sys.stdin); print(j.get('script',{}).get('id',''))")
COURSE_ID="demo-course-pdf-final"

# 3) 设置 course_id
curl -sS -X PUT "$BASE/api/cscl/scripts/$SCRIPT_ID" -H "Content-Type: application/json" -c cookies.txt -b cookies.txt \
  --data "{\"course_id\":\"$COURSE_ID\"}" > /dev/null

# 4) 上传 test.pdf
UPLOAD_RESP=$(curl -sS -X POST "$BASE/api/cscl/courses/$COURSE_ID/docs/upload" -b cookies.txt -c cookies.txt \
  -F "file=@$PDF_PATH;type=application/pdf" -F "title=test.pdf")

# 5) Pipeline run
jq -n --slurpfile s /tmp/spec_final.json '{spec:$s[0]}' > /tmp/pipeline_payload_final.json
PIPE_RESP=$(curl -sS -X POST "$BASE/api/cscl/scripts/$SCRIPT_ID/pipeline/run" \
  -H "Content-Type: application/json" -b cookies.txt -c cookies.txt --data @/tmp/pipeline_payload_final.json)

echo "$PIPE_RESP" | python3 -c "
import json,sys
j=json.load(sys.stdin)
print('run_id:', j.get('run_id'), '| stages:', [s.get('stage_name') for s in j.get('stages',[])])
"
```

## C. 三重证据导出

```bash
mkdir -p docs/evidence_raw
# 1) HTTP 原始响应
echo "$LOGIN_RESP" > docs/evidence_raw/login.json
echo "$CREATE_RESP" > docs/evidence_raw/create_script.json
echo "$UPLOAD_RESP" > docs/evidence_raw/upload.json
echo "$PIPE_RESP" > docs/evidence_raw/pipeline_run.json

# 2) 容器日志
docker compose --env-file .env logs web --since=15m > docs/evidence_raw/web_logs_15m.log
grep -E "pipeline/run|critic|planner|material_generator|refiner" docs/evidence_raw/web_logs_15m.log > docs/evidence_raw/web_logs_keylines.log

# 3) DB stage 记录
RUN_ID=$(echo "$PIPE_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('run_id',''))")
docker compose --env-file .env exec -T postgres psql -U postgres -d teacher_in_loop -c \
  "select run_id, stage_name, status, provider, model from cscl_pipeline_stage_runs where run_id='${RUN_ID}' order by created_at;" \
  > docs/evidence_raw/db_stage_rows.txt
```

---

## 三重证据摘录

### 1) HTTP 原始响应

**upload.json**（摘录）：
```json
{
  "chunks_count": 30,
  "extracted_char_count": 14816,
  "extraction_method": "pypdf_page_text",
  "extracted_text_preview": "1 THE UNIVERSITY OF HONG KONG FACULTY OF EDUCATION Bachelor of Arts and Sciences in Social Data Science [BASc(SDS)] 2024-25 Course Particulars Course code: BSDS3003..."
}
```

**pipeline_run.json**（摘录）：
```json
{
  "run_id": "run_3917c5c652824174",
  "status": "success",
  "stages": [
    {"stage_name": "planner", "status": "success"},
    {"stage_name": "material_generator", "status": "success"},
    {"stage_name": "critic", "status": "success"},
    {"stage_name": "refiner", "status": "success"}
  ]
}
```

### 2) 可 grep 日志（web_logs_keylines.log）

```
PIPELINE_STAGE_JSON {"run_id": "run_3917c5c652824174", "stage_name": "planner", "provider": "openai", "model": "gpt-4o-mini", "latency_ms": 4544, "success": true}
PIPELINE_STAGE_JSON {"run_id": "run_3917c5c652824174", "stage_name": "material_generator", "provider": "openai", "model": "gpt-4o-mini", "latency_ms": 7847, "success": true}
PIPELINE_STAGE_JSON {"run_id": "run_3917c5c652824174", "stage_name": "critic", "provider": "openai", "model": "gpt-4o-mini", "latency_ms": 25754, "success": true}
PIPELINE_STAGE_JSON {"run_id": "run_3917c5c652824174", "stage_name": "refiner", "provider": "openai", "model": "gpt-4o-mini", "latency_ms": 13405, "success": true}
POST /api/cscl/scripts/.../pipeline/run HTTP/1.1 200
```

### 3) DB stage 记录（db_stage_rows.txt）

```
        run_id        |     stage_name     | status  | provider |    model
----------------------+--------------------+---------+----------+-------------
 run_3917c5c652824174 | planner            | success | openai   | gpt-4o-mini
 run_3917c5c652824174 | material_generator | success | openai   | gpt-4o-mini
 run_3917c5c652824174 | critic             | success | openai   | gpt-4o-mini
 run_3917c5c652824174 | refiner            | success | openai   | gpt-4o-mini
(4 rows)
```

---

## 最终结论

1) **PDF 上传成功且提取文本无乱码：是**
   - chunks_count: 30, extracted_char_count: 14816
   - extracted_text_preview 为可读英文，无乱码

2) **Step3（critic）实际执行：是**
   - run_id: `run_3917c5c652824174`
   - HTTP 响应 stages 含 critic 且 status=success
   - 日志 PIPELINE_STAGE_JSON 含 critic success
   - 数据库 cscl_pipeline_stage_runs 含 critic 记录
