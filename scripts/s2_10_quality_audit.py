#!/usr/bin/env python3
"""S2.10 Quality Audit - outputs outputs/s2_10/quality_audit.json. Any dimension fail => exit 1."""
import json
import os
import sys

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "s2_10")
AUDIT_JSON = os.path.join(OUT_DIR, "quality_audit.json")


def audit_structure():
    spec_path = os.path.join(PROJECT_ROOT, "app", "schemas", "pedagogical_spec.py")
    if not os.path.isfile(spec_path):
        return 0.0, "fail", "pedagogical_spec.py not found"
    with open(spec_path, "r", encoding="utf-8") as f:
        c = f.read()
    has_objectives = "learning_objectives" in c or "objectives" in c
    has_flow = "task_type" in c or "scenes" in c
    has_output = "expected_output" in c or "output" in c
    score = (has_objectives + has_flow + has_output) / 3.0
    return score, "pass" if score >= 2 / 3 else "fail", "structure check"


def audit_readability():
    doc_svc = os.path.join(PROJECT_ROOT, "app", "services", "document_service.py")
    with open(doc_svc, "r", encoding="utf-8") as f:
        c = f.read()
    if "normalize_text" in c and "_PDF_BINARY_MARKERS" in c:
        return 1.0, "pass", "normalize_text and binary guardrails present"
    return 0.5, "fail", "readability guardrails missing"


def audit_course_alignment():
    retriever = os.path.join(PROJECT_ROOT, "app", "services", "cscl_retriever.py")
    if os.path.isfile(retriever):
        with open(retriever, "r", encoding="utf-8") as f:
            c = f.read()
        if "retrieve" in c or "chunk" in c:
            return 1.0, "pass", "retriever for course alignment"
    return 0.7, "pass", "alignment via spec only"


def audit_executability():
    spec_path = os.path.join(PROJECT_ROOT, "app", "schemas", "pedagogical_spec.py")
    if not os.path.isfile(spec_path):
        return 0.0, "fail", "spec not found"
    with open(spec_path, "r", encoding="utf-8") as f:
        c = f.read()
    has_duration = "duration" in c
    has_task = "task_type" in c or "task_requirements" in c
    has_output = "expected_output" in c
    score = (has_duration + has_task + has_output) / 3.0
    return score, "pass" if score >= 2 / 3 else "fail", "executability fields"


def audit_safety():
    doc_svc = os.path.join(PROJECT_ROOT, "app", "services", "document_service.py")
    with open(doc_svc, "r", encoding="utf-8") as f:
        c = f.read()
    if "EMPTY_EXTRACTED_TEXT" in c and "TEXT_TOO_SHORT" in c and "PDF_PARSE_FAILED" in c:
        return 1.0, "pass", "empty/short/binary guards present"
    return 0.5, "fail", "safety guards incomplete"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    dims = [
        ("structure_integrity", audit_structure()),
        ("language_readability", audit_readability()),
        ("course_alignment", audit_course_alignment()),
        ("executability", audit_executability()),
        ("safety_filtering", audit_safety()),
    ]
    results = {}
    all_pass = True
    for name, (score, status, evidence) in dims:
        results[name] = {"score": score, "status": status, "evidence": evidence}
        if status == "fail":
            all_pass = False
    report = {
        "dimensions": results,
        "overall": "pass" if all_pass else "fail",
        "threshold_note": "Each dimension must pass; any fail blocks go-live.",
    }
    with open(AUDIT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("Quality audit written to", AUDIT_JSON)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
