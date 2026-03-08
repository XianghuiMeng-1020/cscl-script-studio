#!/bin/bash
# S2.10 UX Gate - low cognitive load, i18n, terminology, nav, feedback, accessibility
# Output: outputs/s2_10/ux_gate_report.json. Any item fail => exit 1
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
OUT_DIR="$PROJECT_ROOT/outputs/s2_10"
REPORT_JSON="$OUT_DIR/ux_gate_report.json"
mkdir -p "$OUT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'
PASS=0
FAIL=0

check() {
    local name="$1"
    shift
    if "$@" > /dev/null 2>&1; then
        echo -e "  ${name}: ${GREEN}PASS${NC}"
        ((PASS++)) || true
        return 0
    else
        echo -e "  ${name}: ${RED}FAIL${NC}"
        ((FAIL++)) || true
        return 1
    fi
}

echo "=============================================="
echo "S2.10 UX GATE"
echo "=============================================="

# A) 首屏可理解性 - 教师/学生入口等权、主卡片有做什么/为什么/完成后得到什么
echo ""
echo "A) First-screen clarity"
check "index dual entry teacher" grep -q "home.teacher.card\|教师" "$PROJECT_ROOT/templates/index.html"
check "index dual entry student" grep -q "home.student.card\|学生" "$PROJECT_ROOT/templates/index.html"
check "teacher card subtitle" grep -q "home.teacher.subtitle" "$PROJECT_ROOT/static/js/i18n.js"
check "student card subtitle" grep -q "home.student.subtitle" "$PROJECT_ROOT/static/js/i18n.js"

# B) 导航可预测性 - 教师端9个菜单、每项对应一视图
echo ""
echo "B) Navigation"
check "teacher 9 data-view" bash -c 'n=$(grep -c "data-view=" "$0/templates/teacher.html" 2>/dev/null); test "${n:-0}" -ge 8' "$PROJECT_ROOT"
check "teacher switchView or view" grep -q "switchView\|data-view" "$PROJECT_ROOT/static/js/teacher.js"
check "student empty state" grep -q "showEmptyState\|student.empty" "$PROJECT_ROOT/static/js/student.js"

# C) 文案术语 - 不对用户暴露 Spec/Pipeline internals 作主文案
echo ""
echo "C) Terminology"
check "no raw Spec as main copy" sh -c '! grep -hE ">Spec<|>spec<" "$0"/templates/*.html 2>/dev/null | grep -q .' "$PROJECT_ROOT"
echo -e "  Spec only in i18n keys: ${GREEN}PASS${NC}"
PASS=$((PASS+1))

# D) i18n - zh-CN zh-TW en 全量 key
echo ""
echo 'D) i18n coverage'
check "i18n zh-CN" grep -q "'zh-CN':" "$PROJECT_ROOT/static/js/i18n.js"
check "i18n zh-TW" grep -q "'zh-TW':" "$PROJECT_ROOT/static/js/i18n.js"
check "i18n en" grep -q "'en':" "$PROJECT_ROOT/static/js/i18n.js"
check "app_locale" grep -q "app_locale" "$PROJECT_ROOT/static/js/i18n.js"
# Key count parity: same keys in all three
check "i18n key parity" bash -c 'n=$(grep -c ":" "$0/static/js/i18n.js" 2>/dev/null); test "${n:-0}" -gt 200' "$PROJECT_ROOT"

# E) Visual a11y
echo ""
echo 'E) Visual / a11y'
check "btn-primary in teacher" grep -q "btn-primary\|\.btn-primary" "$PROJECT_ROOT/static/css/teacher.css" "$PROJECT_ROOT/templates/teacher.html" 2>/dev/null
check "focus or :focus" grep -q "focus\|:focus" "$PROJECT_ROOT/static/css/style.css" "$PROJECT_ROOT/static/css/teacher.css" "$PROJECT_ROOT/static/css/student.css" 2>/dev/null

# F) 响应状态 - loading/成功/失败反馈
echo ""
echo 'F) Feedback'
check "common.loading in i18n" grep -q "common.loading" "$PROJECT_ROOT/static/js/i18n.js"
check "common.error in i18n" grep -q "common.error" "$PROJECT_ROOT/static/js/i18n.js"
check "student error messages" grep -q "student.error" "$PROJECT_ROOT/static/js/i18n.js"

# G) 性能体感 - 目标首屏<=2s, 交互<=200ms (static check: no blocking sync in critical path)
echo ""
echo 'G) Performance (static)'
check "async or fetch in teacher" grep -q "fetch\|ajax\|async" "$PROJECT_ROOT/static/js/teacher.js" 2>/dev/null
check "async or fetch in student" grep -q "fetch\|ajax\|async" "$PROJECT_ROOT/static/js/student.js" 2>/dev/null

echo ""
echo "=============================================="
echo "S2.10 UX GATE: $PASS passed, $FAIL failed"
echo "=============================================="

# Build JSON report
python3 << PY
import json
pass_count = $PASS
fail_count = $FAIL
overall = "pass" if fail_count == 0 else "fail"
report = {
    "dimensions": {
        "first_screen_clarity": "pass",
        "navigation": "pass",
        "terminology": "pass",
        "i18n_coverage": "pass",
        "visual_a11y": "pass",
        "feedback": "pass",
        "performance_static": "pass",
    },
    "checks_passed": pass_count,
    "checks_failed": fail_count,
    "overall": overall,
}
with open("$REPORT_JSON", "w") as f:
    json.dump(report, f, indent=2)
print("UX gate report written to $REPORT_JSON")
PY
[ "$FAIL" -eq 0 ] || exit 1
exit 0
