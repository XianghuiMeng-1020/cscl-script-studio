#!/bin/bash
# S2.10 Concurrency Gate - 20/50 concurrent; 5xx < 0.5%, P95 < 1500ms
# Output: outputs/s2_10/concurrency_report.json
set -uo pipefail

BASE_URL="${BASE_URL:-http://localhost:5001}"
DURATION="${DURATION:-25}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="$PROJECT_ROOT/outputs/s2_10"
REPORT_JSON="$OUT_DIR/concurrency_report.json"
mkdir -p "$OUT_DIR"

run_one() {
    local c="$1"
    local label="$2"
    local url="$3"
    local tmp=$(mktemp)
    local start=$(date +%s)
    local end=$((start + DURATION))
    while [ $(date +%s) -lt "$end" ]; do
        seq 1 "$c" | xargs -P "$c" -I {} curl -sf -o /dev/null -w "%{http_code}\t%{time_total}\n" "$url" 2>/dev/null >> "$tmp" || echo "000	0" >> "$tmp"
    done
    local total=$(wc -l < "$tmp" | tr -d ' \n')
    [ "$total" -eq 0 ] && total=1
    local ok2=$(grep -c '^2' "$tmp" 2>/dev/null) || ok2=0
    local err5=$(grep -c '^5' "$tmp" 2>/dev/null) || err5=0
    local fail=$(grep -c '^000' "$tmp" 2>/dev/null) || fail=0
    local p95_ms=0
    if command -v sort >/dev/null 2>&1; then
        p95_s=$(cut -f2 "$tmp" | sort -n | awk -v n="$total" 'NR >= n*0.95 {print; exit}')
        p95_ms=$(echo "${p95_s:-0} * 1000" | bc 2>/dev/null | cut -d. -f1)
    fi
    rm -f "$tmp"
    echo "$label	$c	$total	$ok2	$err5	$fail	$p95_ms"
}

echo "=============================================="
echo "S2.10 CONCURRENCY GATE (BASE_URL=$BASE_URL, DURATION=${DURATION}s)"
echo "=============================================="

DATA=""
DATA="${DATA}$(run_one 20 "health" "$BASE_URL/api/health")"$'\n'
DATA="${DATA}$(run_one 50 "health_50" "$BASE_URL/api/health")"$'\n'
DATA="${DATA}$(run_one 20 "home" "$BASE_URL/")"$'\n'
DATA="${DATA}$(run_one 20 "teacher" "$BASE_URL/teacher")"$'\n'
DATA="${DATA}$(run_one 20 "student" "$BASE_URL/student")"$'\n'

python3 << PY
import json, sys
lines = """$DATA""".strip().split('\n')
results = []
overall = 'pass'
for line in lines:
    parts = line.split('\t')
    if len(parts) < 7:
        continue
    name, c, total, ok2, err5, fail, p95_ms = parts[0], int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5]), int(parts[6]) if parts[6].isdigit() else 0
    err_total = err5 + fail
    p5xx_pct = (err_total * 10000 // total) / 100.0 if total else 0
    if p5xx_pct >= 0.5 or p95_ms > 1500:
        overall = 'fail'
    results.append({"name": name, "concurrency": c, "total": total, "2xx": ok2, "5xx_plus_fail": err_total, "p5xx_pct": p5xx_pct, "p95_ms": p95_ms})
report = {"results": results, "overall": overall, "threshold_5xx_pct": 0.5, "threshold_p95_ms": 1500}
with open("$REPORT_JSON", "w") as f:
    json.dump(report, f, indent=2)
print("Concurrency report written to $REPORT_JSON")
sys.exit(0 if overall == 'pass' else 1)
PY
exit $?
