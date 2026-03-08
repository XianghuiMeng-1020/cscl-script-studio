#!/bin/bash
# 硬限制复验：使用 /Users/mrealsalvatore/Desktop/test.pdf 走完整上传 + pipeline，验证 Step3(critic) 执行
set -euo pipefail
cd "/Users/mrealsalvatore/Desktop/teacher-in-loop-main"

BASE="http://127.0.0.1:5001"
PDF_PATH="/Users/mrealsalvatore/Desktop/test.pdf"
[ -f "$PDF_PATH" ] || { echo "❌ file not found: $PDF_PATH"; exit 1; }

rm -f cookies.txt

# 1) 登录（user_id/password，Demo@12345）
echo "== 1) Login =="
curl -sS -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt -b cookies.txt \
  --data '{"user_id":"teacher_demo","password":"Demo@12345"}'

# 2) 创建 script + 设置 course_id
echo -e "\n== 2) Create script =="
CREATE_RESP=$(curl -sS -X POST "$BASE/api/cscl/scripts" \
  -H "Content-Type: application/json" -c cookies.txt -b cookies.txt \
  --data '{"title":"pdf-step3-smoke","topic":"Photosynthesis","task_type":"structured_debate","duration_minutes":60}')
SCRIPT_ID=$(echo "$CREATE_RESP" | python3 -c "import json,sys; j=json.load(sys.stdin); print(j.get('script',{}).get('id',''))")
COURSE_ID="demo-course-step3-smoke"

curl -sS -X PUT "$BASE/api/cscl/scripts/$SCRIPT_ID" \
  -H "Content-Type: application/json" -c cookies.txt -b cookies.txt \
  --data "{\"course_id\":\"$COURSE_ID\"}" > /dev/null

# 3) 上传同一本地 PDF（关键限制）
echo -e "\n== 3) Upload test.pdf =="
UPLOAD_RESP=$(curl -sS -X POST "$BASE/api/cscl/courses/$COURSE_ID/docs/upload" \
  -b cookies.txt -c cookies.txt \
  -F "file=@$PDF_PATH;type=application/pdf" -F "title=test.pdf")
echo "chunks_count=$(echo "$UPLOAD_RESP"|python3 -c "import json,sys; j=json.load(sys.stdin); print(j.get('chunks_count','?'))")"
echo "extracted_char_count=$(echo "$UPLOAD_RESP"|python3 -c "import json,sys; j=json.load(sys.stdin); print(j.get('extracted_char_count','?'))")"
echo "extracted_text_preview=$(echo "$UPLOAD_RESP"|python3 -c "import json,sys; j=json.load(sys.stdin); print((j.get('extracted_text_preview') or '')[:150])")..."

# 4) 跑 pipeline
echo -e "\n== 4) Run pipeline =="
cat > /tmp/spec_final.json <<'JSON'
{"course_context":{"subject":"Biology","topic":"Photosynthesis","mode":"sync","description":"Students discuss photosynthesis.","class_size":36,"duration":60},"learning_objectives":{"knowledge":["Explain inputs/outputs of photosynthesis"],"skills":["Use evidence"]},"task_requirements":{"task_type":"structured_debate","collaboration_form":"group","requirements_text":"Claim-evidence-rebuttal.","expected_output":"Debate record."}}
JSON
jq -n --slurpfile s /tmp/spec_final.json '{spec:$s[0]}' > /tmp/pipeline_payload_final.json

PIPE_RESP=$(curl -sS -X POST "$BASE/api/cscl/scripts/$SCRIPT_ID/pipeline/run" \
  -H "Content-Type: application/json" \
  -b cookies.txt -c cookies.txt \
  --data @/tmp/pipeline_payload_final.json)

echo "$PIPE_RESP" | python3 -c "
import json,sys
j=json.load(sys.stdin)
print('run_id:', j.get('run_id'))
print('status:', j.get('status'))
print('stages:', [{'name':s.get('stage_name'),'status':s.get('status')} for s in j.get('stages',[])])
names=[s.get('stage_name') for s in j.get('stages',[])]
if 'critic' in names:
    print('✅ Step3(critic) reached')
else:
    print('❌ Step3(critic) NOT reached')
    sys.exit(2)
"
