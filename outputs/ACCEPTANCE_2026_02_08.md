# 完整验收证据（2026-02-08）

## 执行环境
- 仓库：`/Users/mrealsalvatore/Desktop/teacher-in-loop-main`
- 服务：`http://127.0.0.1:5001`（Docker compose web 5001→5000）
- Demo 账号：`teacher_demo` / `Demo@12345`（需先执行 `docker compose exec web python scripts/seed_demo_users.py`）

---

## 0) 基础检查（命令 + 输出）

```bash
set -euo pipefail
cd "/Users/mrealsalvatore/Desktop/teacher-in-loop-main"
docker compose --env-file .env ps
docker compose --env-file .env port web 5000
curl -sSI http://127.0.0.1:5001/api/health | tr -d '\r' | sed -n '1,20p'
```

输出：
```
NAME                              IMAGE                      ... PORTS
teacher-in-loop-main-postgres-1   postgres:16                ... 0.0.0.0:5432->5432/tcp
teacher-in-loop-main-web-1        teacher-in-loop-main-web   ... 0.0.0.0:5001->5000/tcp

0.0.0.0:5001
HTTP/1.1 200 OK
Server: gunicorn
Content-Type: application/json
...
```

---

## 1) 登录（密码需用 Demo@12345）

```bash
BASE="http://127.0.0.1:5001"
COOKIE="/tmp/cookies_cscl.txt"
rm -f "$COOKIE"

curl -sS -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -c "$COOKIE" -b "$COOKIE" \
  --data '{"user_id":"teacher_demo","password":"Demo@12345"}'
```

输出：
```json
{"message":"Login successful","user":{"id":"teacher_demo","role":"teacher"}}
```

---

## 2) 创建 script

```bash
CREATE_RESP=$(curl -sS -X POST "$BASE/api/cscl/scripts" \
  -H "Content-Type: application/json" -c "$COOKIE" -b "$COOKIE" \
  --data '{"title":"pdf-upload-smoke","topic":"Photosynthesis","task_type":"structured_debate","duration_minutes":60}')
echo "$CREATE_RESP"
SCRIPT_ID=$(echo "$CREATE_RESP" | python3 -c "import json,sys; j=json.load(sys.stdin); print(j.get('script',{}).get('id',''))")
echo "SCRIPT_ID=$SCRIPT_ID"
```

输出：
```json
{"script":{"id":"787cd00d-0d1e-4ab3-8e6f-b68ab6de72f3",...},"success":true}
SCRIPT_ID=787cd00d-0d1e-4ab3-8e6f-b68ab6de72f3
```

---

## 3) 上传 test.pdf

**注意**：原脚本使用的 `PUT /api/cscl/scripts/<script_id>/upload` 返回 404，该路由不存在。

正确流程：
1. 设置 script 的 `course_id`（如 `demo-course-pdf-smoke`）
2. 使用 `POST /api/cscl/courses/<course_id>/docs/upload` 上传

```bash
COURSE_ID="demo-course-pdf-smoke"
PDF_PATH="/Users/mrealsalvatore/Desktop/test.pdf"

# 更新 script 设置 course_id
curl -sS -X PUT "$BASE/api/cscl/scripts/$SCRIPT_ID" \
  -H "Content-Type: application/json" -b "$COOKIE" -c "$COOKIE" \
  --data "{\"title\":\"pdf-upload-smoke\",\"topic\":\"Photosynthesis\",\"course_id\":\"$COURSE_ID\"}"

# 上传 PDF
curl -sS -X POST "$BASE/api/cscl/courses/$COURSE_ID/docs/upload" \
  -b "$COOKIE" -c "$COOKIE" \
  -F "file=@$PDF_PATH;type=application/pdf" \
  -F "title=test.pdf"
```

输出（关键字段）：
```json
{
  "chunks_count": 30,
  "extracted_char_count": 14816,
  "extracted_text_preview": "1 THE UNIVERSITY OF HONG KONG FACULTY OF EDUCATION Bachelor of Arts and Sciences in Social Data Science [BASc(SDS)] 2024-25 Course Particulars Course code: BSDS3003 Course title: Data processing and visualization No. of credits: 6 Course Coordinator Name: Professor LIN Jionghao Email: jionghao@hku.h",
  "extraction_method": "pypdf_page_text",
  "ok": true,
  "success": true,
  "warnings": []
}
```

---

## 4) 拉取脚本详情 / 文档列表

```bash
curl -sS "$BASE/api/cscl/scripts/$SCRIPT_ID" -b "$COOKIE" | jq '.script | {title,course_id,status}'
curl -sS "$BASE/api/cscl/courses/demo-course-pdf-smoke/docs" -b "$COOKIE" | jq '.'
```

输出：
```json
{"title":"pdf-upload-smoke","course_id":"demo-course-pdf-smoke","status":"draft"}
{"success":true,"documents":[{"id":"104fc4ff-e787-44d4-9c6b-35152515eece","title":"test.pdf",...}],"count":1}
```

---

## 5) 跑 pipeline

```bash
cat > /tmp/spec_final.json <<'JSON'
{
  "course_context": {"subject":"Biology","topic":"Photosynthesis","mode":"sync","description":"Students discuss how light affects photosynthesis.","class_size":36,"duration":60},
  "learning_objectives": {"knowledge":["Explain the inputs and outputs of photosynthesis","Describe key stages of photosynthesis"],"skills":["Use evidence to support scientific claims","Collaborate in structured argumentation"]},
  "task_requirements": {"task_type":"structured_debate","collaboration_form":"group","requirements_text":"Teams present claim, evidence, rebuttal, and conclusion.","expected_output":"A group debate record with claim-evidence-rebuttal structure and a short consensus summary."}
}
JSON
jq -n --slurpfile s /tmp/spec_final.json '{spec:$s[0]}' > /tmp/pipeline_payload_final.json

curl -sS -i -X POST "$BASE/api/cscl/scripts/$SCRIPT_ID/pipeline/run" \
  -H "Content-Type: application/json" -b "$COOKIE" -c "$COOKIE" \
  --data @/tmp/pipeline_payload_final.json
```

输出（关键部分）：
```
HTTP/1.1 422 UNPROCESSABLE ENTITY
Content-Type: application/json

{"code":"PIPELINE_FAILED","error":"(raised as a result of Query-invoked autoflush; ...)
(psycopg2.errors.ForeignKeyViolation) insert or update on table \"cscl_evidence_bindings\" violates foreign key constraint \"cscl_evidence_bindings_scene_id_fkey\"
DETAIL:  Key (scene_id)=(scene_0) is not present in table \"cscl_scenes\".
...
"stages":[
  {"stage_name":"planner","status":"success","provider":"openai","model":"gpt-4o-mini"},
  {"stage_name":"material_generator","status":"success","provider":"openai","model":"gpt-4o-mini"}
]}
```

---

## 6) Step3 (critic) 状态提取

```bash
# 从 pipeline 响应解析
curl -sS -X POST "$BASE/api/cscl/scripts/$SCRIPT_ID/pipeline/run" ... | python3 -c "
import json,sys
d=json.load(sys.stdin)
stages=d.get('stages',[])
for s in stages: print(s.get('stage_name'), ':', s.get('status'))
critic=[x for x in stages if x.get('stage_name')=='critic']
print('critic_stage:', 'PRESENT' if critic else 'NOT PRESENT')
"
```

输出：
```
planner : success
material_generator : success
critic_stage: NOT PRESENT
```

---

## 7) Docker 日志证据（最近 15 分钟）

```bash
docker compose --env-file .env logs web --since=15m 2>&1 | grep -E "POST /api/cscl|pipeline|critic|upload"
```

输出：
```
web-1  | "POST /api/cscl/scripts HTTP/1.1" 201
web-1  | "PUT /api/cscl/scripts/.../upload HTTP/1.1" 404
web-1  | "POST /api/cscl/courses/demo-course-pdf-smoke/docs/upload HTTP/1.1" 201
web-1  | SAWarning: Session's state has been changed on a non-active transaction
web-1  | "POST /api/cscl/scripts/.../pipeline/run HTTP/1.1" 422
```

---

## 结论（三段）

### A. PDF 上传是否成功，是否有乱码证据

**结论：PDF 上传成功，无乱码。**

- 正确上传接口：`POST /api/cscl/courses/<course_id>/docs/upload`（原脚本中的 `PUT /api/cscl/scripts/<script_id>/upload` 不存在，会 404）
- 接口返回关键字段：
  - `chunks_count`: 30
  - `extracted_char_count`: 14816
  - `extracted_text_preview`: `"1 THE UNIVERSITY OF HONG KONG FACULTY OF EDUCATION Bachelor of Arts and Sciences in Social Data Science [BASc(SDS)] 2024-25 Course Particulars Course code: BSDS3003 Course title: Data processing and visualization No. of credits: 6 Course Coordinator Name: Professor LIN Jionghao Email: jionghao@hku.h"`
  - `extraction_method`: `pypdf_page_text`
- 抽取文本为可读英文，无乱码。

---

### B. Step3 (critic) 是否跑通

**结论：Step3 (critic) 未跑通。**

- Pipeline 在 material_generator 之后、critic 之前失败
- 失败原因：插入 `cscl_evidence_bindings` 时违反外键约束
  - `scene_id=(scene_0)` 不存在于 `cscl_scenes` 表
  - 原因是 evidence binding 使用了字符串占位符（如 `scene_0`, `scriptlet_0_0`），而 `cscl_scenes` 使用 UUID
- stages 响应仅含 planner（success）、material_generator（success），**无 critic 记录**。

---

### C. 若失败，最小修复建议（仅配置或请求参数层面优先）

**建议：无法仅通过配置或请求参数修复，需改业务逻辑。**

- 根因：`cscl_pipeline_service` 在 material_generator 之后、调用 critic 之前，尝试将 evidence bindings 写入数据库；binding 使用的 `scene_id`/`scriptlet_id` 为字符串占位符（`scene_0`, `scriptlet_0_0`），而 `cscl_scenes`/`cscl_scriptlets` 表主键为 UUID
- 最小修复方向（需改代码）：
  1. 先持久化 scenes 和 scriptlets 到 DB，得到真实 UUID，再用这些 UUID 写入 evidence_bindings；或
  2. 将 evidence_bindings 的持久化移到 critic 和 refiner 完成之后、在写入 scenes/scriptlets 之后执行；或
  3. 在 pipeline 中暂时跳过 evidence_bindings 的持久化，仅做内存传递，以先让 critic/refiner 跑通。

---

## 可复制一键脚本（修正版）

```bash
set -euo pipefail
cd "/Users/mrealsalvatore/Desktop/teacher-in-loop-main"
BASE="http://127.0.0.1:5001"
COOKIE="/tmp/cookies_cscl.txt"
rm -f "$COOKIE"

# 1) 登录（密码 Demo@12345）
curl -sS -X POST "$BASE/api/auth/login" -H "Content-Type: application/json" -c "$COOKIE" -b "$COOKIE" --data '{"user_id":"teacher_demo","password":"Demo@12345"}'

# 2) 创建 script
CREATE_RESP=$(curl -sS -X POST "$BASE/api/cscl/scripts" -H "Content-Type: application/json" -c "$COOKIE" -b "$COOKIE" --data '{"title":"pdf-upload-smoke","topic":"Photosynthesis","task_type":"structured_debate","duration_minutes":60}')
SCRIPT_ID=$(echo "$CREATE_RESP" | python3 -c "import json,sys; j=json.load(sys.stdin); print(j.get('script',{}).get('id',''))")
COURSE_ID="demo-course-pdf-smoke"

# 3) 更新 course_id 并上传 PDF
curl -sS -X PUT "$BASE/api/cscl/scripts/$SCRIPT_ID" -H "Content-Type: application/json" -b "$COOKIE" -c "$COOKIE" --data "{\"title\":\"pdf-upload-smoke\",\"topic\":\"Photosynthesis\",\"course_id\":\"$COURSE_ID\"}"
curl -sS -X POST "$BASE/api/cscl/courses/$COURSE_ID/docs/upload" -b "$COOKIE" -c "$COOKIE" -F "file=@/Users/mrealsalvatore/Desktop/test.pdf;type=application/pdf" -F "title=test.pdf"

# 4) 拉取文档（检查抽取文本）
curl -sS "$BASE/api/cscl/courses/$COURSE_ID/docs" -b "$COOKIE" | jq '.'

# 5) 跑 pipeline（会 422，但 stages 含 planner/material_generator 成功）
jq -n --slurpfile s /tmp/spec_final.json '{spec:$s[0]}' > /tmp/pipeline_payload_final.json 2>/dev/null || true
curl -sS -X POST "$BASE/api/cscl/scripts/$SCRIPT_ID/pipeline/run" -H "Content-Type: application/json" -b "$COOKIE" -c "$COOKIE" --data @/tmp/pipeline_payload_final.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
for s in d.get('stages',[]): print(s['stage_name'], s['status'])
print('critic:', 'yes' if any(x['stage_name']=='critic' for x in d.get('stages',[])) else 'NO')
"
```
