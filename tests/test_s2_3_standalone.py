"""S2.3 BLOCKER - Standalone tests (no Flask app). Run: python tests/test_s2_3_standalone.py"""
import sys
import os

_base = os.path.join(os.path.dirname(__file__), '..')

def test_i18n_keys():
    with open(os.path.join(_base, 'static', 'js', 'i18n.js'), 'r', encoding='utf-8') as f:
        c = f.read()
    assert "Validate Teaching Plan Settings" in c
    assert "校验教学目标设置" in c
    assert "驗證教學目標設定" in c
    assert "app_locale" in c

def test_home_data_i18n():
    with open(os.path.join(_base, 'templates', 'index.html'), encoding='utf-8') as f:
        c = f.read()
    assert 'data-i18n="home.title"' in c
    assert 'data-i18n="home.teacher.card"' in c

def test_teacher_sidebar_i18n():
    with open(os.path.join(_base, 'templates', 'teacher.html'), encoding='utf-8') as f:
        c = f.read()
    for k in ['teacher.sidebar.dashboard', 'teacher.sidebar.spec', 'teacher.spec.validate']:
        assert k in c

def test_btn_primary_css():
    with open(os.path.join(_base, 'static', 'css', 'style.css'), encoding='utf-8') as f:
        c = f.read()
    assert '.btn-primary' in c
    assert 'min-height' in c or '40px' in c

def test_pdf_binary_markers_regex():
    with open(os.path.join(_base, 'app', 'services', 'document_service.py'), encoding='utf-8') as f:
        c = f.read()
    assert '_PDF_BINARY_MARKERS' in c
    assert '%PDF-' in c
    assert 'xref' in c or 'stream' in c

def test_spec_not_in_visible():
    import re
    for name in ['index.html', 'teacher.html', 'student.html']:
        with open(os.path.join(_base, 'templates', name), encoding='utf-8') as f:
            content = f.read()
        for m in re.finditer(r'>([^<]+)<', content.split('<script')[0]):
            if re.search(r'\bSpec\b', m.group(1)):
                raise AssertionError(f"Found 'Spec' in {name}: {repr(m.group(1))}")

if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_') and callable(fn):
            try:
                fn()
                print(f"PASS: {name}")
            except Exception as e:
                print(f"FAIL: {name} - {e}")
                sys.exit(1)
    print("\nAll standalone tests passed.")
