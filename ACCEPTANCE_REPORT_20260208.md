# 完整验收报告 2026-02-08

## 执行环境
- 仓库：`/Users/mrealsalvatore/Desktop/teacher-in-loop-main`
- 服务：`http://127.0.0.1:5001`（Docker Compose）
- 测试 PDF：`/Users/mrealsalvatore/Desktop/test.pdf`
- Demo 账号：`teacher_demo` / `Demo@12345`（需先执行 `docker compose exec web python scripts/seed_demo_users.py`）

---

## 可复制执行命令（修正版）

```bash
set -euo pipefail
cd "/Users/mrealsalvatore/Desktop/teacher-in-loop-main"

# 0. 基础检查
docker compose --env-file .env ps
curl -sSI http://127.0.0.1:5001/api/health | head -5

# 1. Seed demo 账号（若尚未执行）
docker compose --env-file .env exec web python scripts/seed_demo_users.py

# 2. 登录
BASE="http://127.0.0.1:5001"
COOKIE="/tmp/cookies_cscl.txt"
rm -f "$COOKIE"
curl -sS -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" -c "$COOKIE" -b "$COOKIE" \
  --data '{"user_id":"teacher_demo","password":"Demo@12345"}'

# 3. 创建 script
CREATE_RESP=$(curl -sS -X POST "$BASE/api/cscl/scripts" \
  -H "Content-Type: application/json" -c "$COOKIE" -b "$COOKIE" \
  --data '{"title":"pdf-upload-smoke","topic":"Photosynthesis","task_type":"structured_debate","duration_minutes":60}')
SCRIPT_ID=$(echo "$CREATE_RESP" | python3 -c "import json,sys; j=json.load(sys.stdin); print(j.get('script',{}).get('id',''))")
COURSE_ID="demo-course-pdf-smoke"

# 4. 更新 script 设置 course_id
curl -sS -X PUT "$BASE/api/cscl/scripts/$SCRIPT_ID" \
  -H "Content-Type: application/json" -b "$COOKIE" -c "$COOKIE" \
  --data "{\"title\":\"pdf-upload-smoke\",\"topic\":\"Photosynthesis\",\"course_id\":\"$COURSE_ID\"}"

# 5. 上传 PDF（正确路由：POST /api/cscl/courses/<course_id>/docs/upload）
curl -sS -X POST "$BASE/api/cscl/courses/$COURSE_ID/docs/upload" \
  -b "$COOKIE" -c "$COOKIE" \
  -F "file=@/Users/mrealsalvatore/Desktop/test.pdf;type=application/pdf" \
  -F "title=test.pdf"

# 6. 拉取文档列表
curl -sS "$BASE/api/cscl/courses/$COURSE_ID/docs" -b "$COOKIE" | jq .

# 7. 跑 pipeline
jq -n --slurpfile s /tmp/spec_final.json '{spec:$s[0]}' > /tmp/pipeline_payload_final.json
curl -sS -X POST "$BASE/api/cscl/scripts/$SCRIPT_ID/pipeline/run" \
  -H "Content-Type: application/json" -b "$COOKIE" -c "$COOKIE" \
  --data @/tmp/pipeline_payload_final.json | jq '.stages[]|{stage_name,status,error}'
```

---

## 原始输出摘要

### PDF 上传接口返回（201 CREATED）
```json
{
  "chunks_count": 30,
  "detected_type": "pdf",
  "doc_id": "104fc4ff-e787-44d4-9c6b-35152515eece",
  "extracted_char_count": 14816,
  "extraction_method": "pypdf_page_text",
  "extracted_text_preview": "1 THE UNIVERSITY OF HONG KONG FACULTY OF EDUCATION Bachelor of Arts and Sciences in Social Data Science [BASc(SDS)] 2024-25 Course Particulars Course code: BSDS3003 Course title: Data processing and visualization No. of credits: 6 Course Coordinator Name: Professor LIN Jionghao Email: jionghao@hku.h",
  "ok": true,
  "success": true,
  "warnings": []
}
```

### Pipeline 响应（422 UNPROCESSABLE ENTITY）
- **stages**：仅 2 个——`planner`（success）、`material_generator`（success）
- **critic**：未出现在 stages 中（pipeline 在 critic 前失败）
- **top_error**：`ForeignKeyViolation: insert or update on table "cscl_evidence_bindings" violates foreign key constraint "cscl_evidence_bindings_scene_id_fkey" - Key (scene_id)=(scene_0) is not present in table "cscl_scenes"`

### 日志片段
```
web-1  | POST /api/cscl/courses/demo-course-pdf-smoke/docs/upload HTTP/1.1 201
web-1  | POST /api/cscl/scripts/.../pipeline/run HTTP/1.1 422
web-1  | SAWarning: Session's state has been changed on a non-active transaction
```

---

## 三段式结论

### A. PDF 上传是否成功，是否有乱码证据

**结论：成功，无乱码。**

- 接口：`POST /api/cscl/courses/<course_id>/docs/upload`（不是 `PUT /api/cscl/scripts/<id>/upload`，后者 404）
- 关键字段：`chunks_count: 30`、`extracted_char_count: 14816`、`extraction_method: pypdf_page_text`
- `extracted_text_preview` 为可读英文："1 THE UNIVERSITY OF HONG KONG FACULTY OF EDUCATION Bachelor of Arts and Sciences in Social Data Science..."

### B. Step3（critic）是否跑通

**结论：未跑通。critic 未被调用。**

- `stages` 仅包含 `planner`、`material_generator`，均为 success
- `critic` 未出现在 stages 中
- 失败发生在 material_generator 之后、critic 之前：插入 `cscl_evidence_bindings` 时触发外键约束 `scene_id=scene_0` 不存在于 `cscl_scenes`

### C. 若失败，最小修复建议

1. **问题定位**：pipeline 在保存 evidence_bindings 时使用了 `scene_0`、`scriptlet_0_0` 等字符串 ID，而数据库期望的是 `cscl_scenes`、`cscl_scriptlets` 表中已存在的 UUID。
2. **修复层级**：需修改 pipeline 逻辑（`cscl_pipeline_service.py` 或相关持久化代码），先创建并提交 scenes/scriptlets，再插入 evidence_bindings，并确保使用正确的 scene_id/scriptlet_id（UUID）而非占位字符串。
3. **纯配置/参数层面**：无法通过配置或请求参数解决，必须改代码中 evidence_bindings 的插入顺序与 ID 映射逻辑。
