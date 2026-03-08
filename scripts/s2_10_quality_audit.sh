#!/bin/bash
# S2.10 Quality Audit Gate - runs s2_10_quality_audit.py, outputs outputs/s2_10/quality_audit.json
# Any dimension fail => exit 1
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
python3 scripts/s2_10_quality_audit.py
exit $?
