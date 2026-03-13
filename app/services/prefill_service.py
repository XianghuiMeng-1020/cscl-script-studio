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


def extract_prefill(text: str) -> Dict[str, Any]:
    """
    From extracted document text, suggest form fields for course_context, learning_objectives, task_requirements.
    Returns flat suggestions with value/source_span/confidence/needs_confirmation. Empty/low-quality doc -> warnings, no block.
    """
    warnings: List[str] = []
    if not text or not text.strip():
        return {"suggestions": {}, "warnings": ["文档无文本，无法提取建议。"], "degraded": True}

    raw = text.strip()
    if len(raw) < 80:
        warnings.append("文档较短，建议可能不完整，请核对后使用。")

    suggestions: Dict[str, Any] = {}
    valid_task_types = get_valid_task_type_ids()

    # Subject / course title: first line or first sentence, max 80 chars to avoid long blocks
    _COURSE_TITLE_MAX = 80
    subject_candidates = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line or len(line) < 2:
            continue
        if re.search(r"课程|course|subject|课名", line, re.I):
            subject_candidates.append((line[:_COURSE_TITLE_MAX], 0.8))
        elif not subject_candidates and 3 <= len(line) <= _COURSE_TITLE_MAX:
            subject_candidates.append((line[:_COURSE_TITLE_MAX], 0.5))
    if subject_candidates:
        best = subject_candidates[0]
        suggestions["course_title"] = _field(best[0], best[0], best[1], best[1] < 0.7)
    else:
        first_line = _first_line(raw, _COURSE_TITLE_MAX)
        suggestions["course_title"] = _field(first_line, first_line, 0.4 if first_line else 0.0, True)

    # Topic: single line, max 60 chars; prefer line with "主题|topic|单元"
    _TOPIC_MAX = 60
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip() and len(ln.strip()) >= 2]
    topic_val = ""
    for line in lines[:5]:
        if re.search(r"主题|topic|单元", line, re.I):
            topic_val = line[:_TOPIC_MAX]
            break
    if not topic_val and len(lines) >= 2:
        topic_val = (lines[1] or "")[:_TOPIC_MAX]
    suggestions["topic"] = _field(
        topic_val or "",
        topic_val,
        0.6 if topic_val else 0.0,
        not topic_val or len(topic_val) < 3,
    )

    # Description (Course Context): first 1–2 paragraphs or 200–300 chars
    _DESC_MAX = 280
    desc = raw.replace("\n\n", "\n").split("\n")
    desc_block = " ".join(desc[:4]).strip()[:_DESC_MAX] if desc else ""
    suggestions["description"] = _field(
        desc_block or "",
        desc_block[:200] if desc_block else "",
        0.5 if desc_block else 0.0,
        True,
    )

    # Learning outcomes: max 8 items, max 120 chars per item
    _OBJ_LINE_MAX = 120
    objectives: List[str] = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        if re.search(r"目标|objective|outcome|learning|能力", line, re.I):
            objectives.append(line[:_OBJ_LINE_MAX])
        elif re.match(r"^[\d•\-*]\s*", line) and 5 <= len(line) <= 200:
            objectives.append(line.lstrip("0123456789•\-* ")[:_OBJ_LINE_MAX])
    if not objectives and len(raw) > 100 and lines:
        objectives = [lines[i][:_OBJ_LINE_MAX] for i in range(min(3, len(lines))) if 10 <= len(lines[i]) <= 200]
    suggestions["learning_outcomes"] = _field(
        objectives[:8],
        "\n".join(objectives[:3]) if objectives else "",
        0.6 if objectives else 0.0,
        not objectives or len(objectives) < 2,
    )

    # Task type: default structured_debate if not detected (backend will map from collaboration_purpose)
    task_type = "structured_debate"
    for tt in valid_task_types:
        if tt in raw.lower() or tt.replace("_", " ") in raw.lower():
            task_type = tt
            break
    suggestions["task_type"] = _field(task_type, task_type, 0.5, True)

    # Expected output: no prefill (backend infers from purpose/objectives); empty value to avoid Chinese "小组产出"
    suggestions["expected_output"] = _field("", "", 0.0, True)

    # Requirements text: short summary or placeholder
    req_val = ""
    for line in raw.split("\n"):
        line = line.strip()
        if re.search(r"要求|requirement|评分|grading", line, re.I) and 10 <= len(line) <= 400:
            req_val = line
            break
    if not req_val:
        req_val = "请根据课程目标补充协作与证据要求。"
    suggestions["requirements_text"] = _field(req_val, req_val[:150], 0.4 if req_val else 0.3, True)

    # Class size / duration: numbers
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
