"""S2.17: Teacher page click flow - template and script consistency; no inline goToStep."""
import pytest
from pathlib import Path


def test_teacher_html_step_buttons_have_data_action_no_onclick_go_to_step():
    """Step buttons must have data-action and must NOT have onclick=goToStep."""
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "teacher.html").read_text(encoding="utf-8")
    assert 'data-action="import-outline"' in html
    assert 'data-action="validate-goals"' in html
    assert 'data-action="run-pipeline"' in html
    assert 'id="btnImport"' in html
    assert 'id="btnValidate"' in html
    assert 'id="btnGenerate"' in html
    assert 'onclick="goToStep(1)"' not in html
    assert 'onclick="goToStep(2)"' not in html
    assert 'onclick="goToStep(3)"' not in html
    assert 'onclick="goToStep(4)"' not in html
    assert 'onclick="event.stopPropagation(); goToStep(' not in html


def test_teacher_js_has_four_phase_logs():
    """teacher.js must contain [teacher] script loaded, dom ready, bind start, bind end."""
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "js" / "teacher.js").read_text(encoding="utf-8")
    assert "[teacher] script loaded" in js
    assert "[teacher] dom ready" in js
    assert "[teacher] bind start" in js
    assert "[teacher] bind end" in js


def test_teacher_js_has_delegation_bind_logs():
    """teacher.js must log delegation bind start and end."""
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "js" / "teacher.js").read_text(encoding="utf-8")
    assert "delegation bind start" in js
    assert "delegation bind end" in js


def test_teacher_js_has_click_captured_log():
    """teacher.js click handler must log click captured action/id/class."""
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "js" / "teacher.js").read_text(encoding="utf-8")
    assert "click captured" in js


def test_teacher_js_has_fatal_logger():
    """teacher.js must register [teacher][fatal] for onerror/unhandledrejection."""
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "js" / "teacher.js").read_text(encoding="utf-8")
    assert "[teacher][fatal]" in js
    assert "onerror" in js or "window.onerror" in js
    assert "unhandledrejection" in js


def test_teacher_js_show_loading_false_in_catches():
    """All DOMContentLoaded catch blocks should call showLoading(false)."""
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "js" / "teacher.js").read_text(encoding="utf-8")
    assert "showLoading(false)" in js
    assert js.count("showLoading(false)") >= 3


def test_loading_overlay_hidden_has_opacity_and_pointer_events():
    """style.css .loading-overlay.hidden must have opacity and pointer-events."""
    root = Path(__file__).resolve().parents[1]
    css = (root / "static" / "css" / "style.css").read_text(encoding="utf-8")
    assert ".loading-overlay.hidden" in css
    assert "pointer-events" in css
    assert "opacity" in css
