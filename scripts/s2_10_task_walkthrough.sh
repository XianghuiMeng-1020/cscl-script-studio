#!/bin/bash
# S2.10 Task Walkthrough - demo account teacher/student core tasks; output steps and success
# Threshold: teacher core one-shot >= 95%, student >= 95%; teacher <=7 steps, student <=5 steps
set -uo pipefail
BASE_URL="${BASE_URL:-http://localhost:5001}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="$PROJECT_ROOT/outputs/s2_10"
mkdir -p "$OUT_DIR"

echo "=============================================="
echo "S2.10 TASK WALKTHROUGH (smoke)"
echo "=============================================="

# Teacher path: login -> create -> upload -> validate -> run -> quality -> export (smoke: endpoints exist and return 200/401/403 as expected)
TEACHER_STEPS=0
TEACHER_OK=0
# 1) GET /teacher 200
if curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/teacher" | grep -q 200; then ((TEACHER_OK++)); fi
((TEACHER_STEPS++))
# 2) GET /api/health 200
if curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/api/health" | grep -q 200; then ((TEACHER_OK++)); fi
((TEACHER_STEPS++))
# 3) POST /api/cscl/spec/validate (public or 401)
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d '{"course_context":{"subject":"S","topic":"T","class_size":30,"mode":"sync","duration":90},"learning_objectives":{"knowledge":["K"],"skills":["S"]},"task_requirements":{"task_type":"debate","expected_output":"O","collaboration_form":"group"}}' "$BASE_URL/api/cscl/spec/validate")
if [ "$CODE" = "200" ] || [ "$CODE" = "401" ] || [ "$CODE" = "403" ]; then ((TEACHER_OK++)); fi
((TEACHER_STEPS++))
echo "Teacher smoke: $TEACHER_OK/$TEACHER_STEPS steps OK"

# Student path: GET /student 200, GET /student?script_id=xxx 200 or 401/403
STUDENT_STEPS=0
STUDENT_OK=0
if curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/student" | grep -q 200; then ((STUDENT_OK++)); fi
((STUDENT_STEPS++))
if curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/student?script_id=test" | grep -qE '200|401|403'; then ((STUDENT_OK++)); fi
((STUDENT_STEPS++))
echo "Student smoke: $STUDENT_OK/$STUDENT_STEPS steps OK"

# Threshold: 95% one-shot (we have 3 and 2 steps; 100% required for this smoke)
TEACHER_PCT=$(( TEACHER_OK * 100 / TEACHER_STEPS ))
STUDENT_PCT=$(( STUDENT_OK * 100 / STUDENT_STEPS ))
echo "Teacher: ${TEACHER_PCT}%, Student: ${STUDENT_PCT}%"
if [ "$TEACHER_PCT" -ge 95 ] && [ "$STUDENT_PCT" -ge 95 ]; then
    echo "PASS: task walkthrough thresholds met"
    exit 0
fi
echo "FAIL: task walkthrough below 95%"
exit 1
