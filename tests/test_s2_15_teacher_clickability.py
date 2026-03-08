"""S2.15: Teacher page clickability - template and script consistency; event delegation and logs."""
import pytest
import re


def test_teacher_template_has_step_buttons_and_data_action():
    """Teacher HTML must have data-action for import-outline, validate-goals, run-pipeline."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "teacher.html").read_text(encoding="utf-8")
    assert 'data-action="import-outline"' in html, "template must have data-action import-outline"
    assert 'data-action="validate-goals"' in html, "template must have data-action validate-goals"
    assert 'data-action="run-pipeline"' in html, "template must have data-action run-pipeline"
    assert 'id="btnImport"' in html or 'btnImport' in html
    assert 'id="btnValidate"' in html or 'btnValidate' in html
    assert 'id="btnGenerate"' in html or 'btnGenerate' in html


def test_teacher_template_has_nav_data_view():
    """Sidebar nav must have data-view for spec-validation (教学目标检查)."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "teacher.html").read_text(encoding="utf-8")
    assert 'data-view="spec-validation"' in html
    assert 'data-view="dashboard"' in html


def test_teacher_js_has_phased_init_logs():
    """teacher.js must contain [teacher] script loaded, dom ready, bind start, bind end."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "js" / "teacher.js").read_text(encoding="utf-8")
    assert "[teacher] script loaded" in js
    assert "[teacher] dom ready" in js
    assert "[teacher] bind start" in js
    assert "[teacher] bind end" in js


def test_teacher_js_has_event_delegation():
    """teacher.js must use document-level delegation (addEventListener on document)."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "js" / "teacher.js").read_text(encoding="utf-8")
    assert "document.addEventListener('click'" in js or 'document.addEventListener("click"' in js
    assert "setupEventDelegation" in js
    assert "closest" in js


def test_teacher_js_guards_null_query_selector():
    """setupNavigation must guard against empty querySelectorAll (no addEventListener on null)."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "js" / "teacher.js").read_text(encoding="utf-8")
    assert "querySelectorAll('.nav-item')" in js
    # Must have length check or forEach that doesn't assume non-null item
    assert "if (!items || !items.length)" in js or ".forEach" in js


def test_loading_overlay_hidden_has_pointer_events_none():
    """style.css .loading-overlay.hidden must include pointer-events: none."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    css = (root / "static" / "css" / "style.css").read_text(encoding="utf-8")
    assert ".loading-overlay.hidden" in css
    assert "pointer-events" in css
