"""C3: Prefill service — extract suggested form fields from document text (rule-based)."""
import re
from typing import Dict, Any, List
from app.services.task_type_config import get_valid_task_type_ids


def _field(value: Any, source_span: str, confidence: float, needs_confirmation: bool) -> Dict[str, Any]:
    return {
        "value": value,
        "source_span": source_span[:200] if source_span else "",
        "confidence": round(confidence, 2),
        "needs_confirmation": needs_confirmation,
    }


def _first_line(text: str, max_len: int = 200) -> str:
    if not text or not text.strip():
        return ""
    line = text.strip().split("\n")[0].strip()
    return line[:max_len] if len(line) > max_len else line


def _is_boilerplate_line(line: str) -> bool:
    """True if line looks like institutional header or admin info."""
    upper = line.upper()
    if len(line) > 60 and any(x in upper for x in ("UNIVERSITY", "FACULTY", "DEPARTMENT", "COLLEGE")):
        return True
    if re.search(r"Course\s+Coordinator|Professor\s+\w+|Email\s*:|Telephone|Office\s*:|Room\s+\d+", line, re.I):
        return True
    return False


def _strip_leading_number(s: str) -> str:
    """Remove leading digits and space (e.g. '1 THE UNIVERSITY...' -> 'THE UNIVERSITY...')."""
    return re.sub(r"^\s*\d+\s*", "", s).strip()


def extract_prefill(text: str) -> Dict[str, Any]:
    """
    From extracted document text, suggest form fields for course_context, learning_objectives, task_requirements.
    Returns flat suggestions with value/source_span/confidence/needs_confirmation. Empty/low-quality doc -> warnings.
    """
    warnings: List[str] = []
    if not text or not text.strip():
        return {"suggestions": {}, "warnings": ["Document has no text; cannot extract suggestions."], "degraded": True}

    raw = text.strip()
    if len(raw) < 80:
        warnings.append("Document is short; suggestions may be incomplete. Please review before use.")

    suggestions: Dict[str, Any] = {}
    valid_task_types = get_valid_task_type_ids()
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip() and len(ln.strip()) >= 2]

    # Course title: max 50 chars; prefer "Course title:" / "Course code:" / "课程名称：" value; exclude boilerplate
    _COURSE_TITLE_MAX = 50
    course_title_val = ""
    for line in lines[:15]:
        if _is_boilerplate_line(line):
            continue
        m = re.search(r"(?:Course\s+title|Course\s+code|课程名称|课名)\s*[：:]\s*(.+)", line, re.I)
        if m:
            course_title_val = _strip_leading_number(m.group(1).strip())[:_COURSE_TITLE_MAX]
            break
        if not course_title_val and 3 <= len(line) <= _COURSE_TITLE_MAX and not re.search(r"^\d", line):
            course_title_val = line[:_COURSE_TITLE_MAX]
            break
    if not course_title_val:
        first = _first_line(raw, _COURSE_TITLE_MAX)
        if first and not _is_boilerplate_line(first):
            course_title_val = _strip_leading_number(first)[:_COURSE_TITLE_MAX]
    suggestions["course_title"] = _field(
        course_title_val or "",
        course_title_val,
        0.6 if course_title_val else 0.0,
        not course_title_val or len(course_title_val) < 3,
    )

    # Topic: max 40 chars; prefer "Course title:" or "主题|topic|单元" line; exclude boilerplate
    _TOPIC_MAX = 40
    topic_val = ""
    for line in lines[:10]:
        if _is_boilerplate_line(line):
            continue
        m = re.search(r"(?:Course\s+title|主题|topic|单元)\s*[：:]\s*(.+)", line, re.I)
        if m:
            topic_val = _strip_leading_number(m.group(1).strip())[:_TOPIC_MAX]
            break
        if re.search(r"主题|topic|单元", line, re.I) and len(line) <= 80:
            topic_val = _strip_leading_number(line)[:_TOPIC_MAX]
            break
    if not topic_val and len(lines) >= 2:
        for line in lines[1:5]:
            if not _is_boilerplate_line(line) and 3 <= len(line) <= 80:
                topic_val = line[:_TOPIC_MAX]
                break
    suggestions["topic"] = _field(
        topic_val or "",
        topic_val,
        0.6 if topic_val else 0.0,
        not topic_val or len(topic_val) < 3,
    )

    # Description (Course Context): first 2 non-boilerplate lines, max 200 chars
    _DESC_MAX = 200
    desc_lines = []
    for line in lines[:6]:
        if _is_boilerplate_line(line) or len(line) < 10:
            continue
        desc_lines.append(line)
        if len(desc_lines) >= 2:
            break
    desc_block = " ".join(desc_lines).strip()[:_DESC_MAX] if desc_lines else ""
    suggestions["description"] = _field(
        desc_block or "",
        desc_block[:200] if desc_block else "",
        0.5 if desc_block else 0.0,
        True,
    )

    # Learning outcomes: max 8 items, 120 chars each; only list items (bullet/number start)
    _OBJ_LINE_MAX = 120
    objectives: List[str] = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line or len(line) < 5:
            continue
        # Skip section headers like "Learning outcomes:" / "Learning objectives:"
        if re.match(r"^(Learning\s+outcomes?|Learning\s+objectives?|目标|能力)\s*[：:]?\s*$", line, re.I):
            continue
        if re.match(r"^[\d•\-*]\s+", line) and 5 <= len(line) <= 200:
            objectives.append(line.lstrip("0123456789•\-* ")[:_OBJ_LINE_MAX])
        elif re.search(r"目标|objective|outcome|能力", line, re.I) and 10 <= len(line) <= 200 and re.match(r"^[\d•\-*]", line):
            objectives.append(line.lstrip("0123456789•\-* ")[:_OBJ_LINE_MAX])
    if not objectives and len(raw) > 100:
        for line in lines[2:8]:
            if re.match(r"^[\d•\-*]\s+", line) and 10 <= len(line) <= 200:
                objectives.append(line.lstrip("0123456789•\-* ")[:_OBJ_LINE_MAX])
    suggestions["learning_outcomes"] = _field(
        objectives[:8],
        "\n".join(objectives[:3]) if objectives else "",
        0.6 if objectives else 0.0,
        not objectives or len(objectives) < 2,
    )

    # Task type: default structured_debate (backend maps from collaboration_purpose)
    task_type = "structured_debate"
    for tt in valid_task_types:
        if tt in raw.lower() or tt.replace("_", " ") in raw.lower():
            task_type = tt
            break
    suggestions["task_type"] = _field(task_type, task_type, 0.5, True)

    # Expected output: no prefill (backend infers)
    suggestions["expected_output"] = _field("", "", 0.0, True)

    # Requirements text: empty default (no Chinese placeholder)
    req_val = ""
    for line in raw.split("\n"):
        line = line.strip()
        if re.search(r"要求|requirement|评分|grading", line, re.I) and 10 <= len(line) <= 400:
            req_val = line[:150]
            break
    suggestions["requirements_text"] = _field(req_val, req_val[:150] if req_val else "", 0.4 if req_val else 0.3, True)

    # Class size / duration
    class_size = 30
    m = re.search(r"(\d+)\s*人|class\s*size\s*[:=]?\s*(\d+)|人数\s*[:：]?\s*(\d+)", raw, re.I)
    if m:
        class_size = int(m.group(1) or m.group(2) or m.group(3) or 30)
    suggestions["class_size"] = _field(class_size, str(class_size), 0.6, False)
    duration = 90
    m = re.search(r"(\d+)\s*分钟|(\d+)\s*min|duration\s*[:=]?\s*(\d+)", raw, re.I)
    if m:
        duration = int(m.group(1) or m.group(2) or m.group(3) or 90)
    suggestions["duration"] = _field(duration, str(duration), 0.5, False)

    return {
        "suggestions": suggestions,
        "warnings": warnings,
        "degraded": len(raw) < 80,
    }
