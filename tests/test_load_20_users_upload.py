"""
20-user load test: seed 20 teachers, each uploads a different demo file, then verify content.
Uses in-process test client (no live server). Run: pytest tests/test_load_20_users_upload.py -v
"""
import os
import tempfile
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Add project root
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DEMO_DIR = os.path.join(ROOT, "scripts", "demo_files_20")
PASSWORD = "LoadTest@20"
NUM_USERS = 20


def _create_app(db_url="sqlite:///:memory:"):
    os.environ["USE_DB_STORAGE"] = "true"
    os.environ["DATABASE_URL"] = db_url
    os.environ["SECRET_KEY"] = "test-secret-load"
    os.environ["TESTING"] = "true"
    os.environ["LLM_PROVIDER"] = "mock"
    import importlib
    import app.config
    importlib.reload(app.config)
    from app import create_app
    app_instance = create_app()
    app_instance.config["TESTING"] = True
    app_instance.config["USE_DB_STORAGE"] = True
    app_instance.config["DATABASE_URL"] = db_url
    return app_instance


@pytest.fixture(scope="module")
def app():
    return _create_app("sqlite:///:memory:")


@pytest.fixture(scope="module")
def db_setup(app):
    from app.db import db
    from app.models import User, UserRole
    with app.app_context():
        db.create_all()
        for i in range(1, NUM_USERS + 1):
            uid = f"teacher_load_{i}"
            u = db.session.get(User, uid)
            if u is None:
                u = User(id=uid, role=UserRole.TEACHER, created_at=datetime.utcnow())
                u.set_password(PASSWORD)
                db.session.add(u)
        db.session.commit()
    yield
    with app.app_context():
        db.session.remove()
        db.drop_all()


def get_demo_files():
    out = []
    for i in range(1, NUM_USERS + 1):
        for ext in (".md", ".txt"):
            path = os.path.join(DEMO_DIR, f"demo_syllabus_{i:02d}{ext}")
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    content = f.read()
                mime = "text/markdown" if ext == ".md" else "text/plain"
                out.append((i, os.path.basename(path), content, mime))
                break
    return out


def test_20_demo_files_exist():
    files = get_demo_files()
    assert len(files) == NUM_USERS, f"Need {NUM_USERS} demo files in scripts/demo_files_20. Run scripts/gen_20_demo_files.py"


def test_20_users_upload_and_verify(app, db_setup):
    """Each of 20 users: login, create script, upload one demo file, list docs, verify extracted text."""
    from app.db import db
    client = app.test_client()
    demo_files = get_demo_files()
    assert len(demo_files) == NUM_USERS

    errors = []
    for (user_index, filename, file_bytes, mime_type) in demo_files:
        uid = f"teacher_load_{user_index}"
        course_id = f"course_user_{user_index}"

        # Login
        r = client.post("/api/auth/login", json={"user_id": uid, "password": PASSWORD})
        if r.status_code != 200:
            errors.append(f"User {user_index}: login {r.status_code}")
            continue

        # Create script
        r = client.post(
            "/api/cscl/scripts",
            json={"title": f"Load script {user_index}", "topic": f"Topic {user_index}", "course_id": course_id},
        )
        if r.status_code not in (200, 201):
            errors.append(f"User {user_index}: create_script {r.status_code}")
            continue

        # Upload document (multipart: file + title)
        from io import BytesIO
        r = client.post(
            f"/api/cscl/courses/{course_id}/docs/upload",
            data={
                "title": filename,
                "file": (BytesIO(file_bytes), filename, mime_type),
            },
        )
        if r.status_code not in (200, 201):
            errors.append(f"User {user_index}: upload {r.status_code} {r.get_data(as_text=True)[:200]}")
            continue
        body = r.get_json()
        if body.get("error") or body.get("code") in ("PDF_PARSE_FAILED", "UNSUPPORTED_FILE_TYPE", "TEXT_TOO_SHORT"):
            errors.append(f"User {user_index}: upload error {body.get('error')} code={body.get('code')}")
            continue
        doc = body.get("document") or body.get("doc")
        if not doc:
            errors.append(f"User {user_index}: no document in response")
            continue

        full_text = body.get("extracted_text") or body.get("extracted_text_preview") or ""
        marker = f"DEMO-{user_index:02d}"
        if marker not in full_text:
            errors.append(f"User {user_index}: content mismatch (marker {marker} not in extracted text)")

        # List docs
        r = client.get(f"/api/cscl/courses/{course_id}/docs")
        if r.status_code != 200:
            errors.append(f"User {user_index}: list_docs {r.status_code}")
            continue
        list_body = r.get_json()
        docs = list_body.get("documents") if isinstance(list_body, dict) else list_body
        if not isinstance(docs, list) or not any(d.get("id") == doc.get("id") for d in docs):
            errors.append(f"User {user_index}: list_docs missing uploaded doc")

    assert not errors, "Errors:\n" + "\n".join(errors)


def _run_one_user_upload(app, user_index, filename, file_bytes, mime_type):
    """Run login -> create script -> upload -> list -> verify for one user (in app context)."""
    from io import BytesIO
    errors = []
    with app.app_context():
        client = app.test_client()
        uid = f"teacher_load_{user_index}"
        course_id = f"course_user_{user_index}"
        r = client.post("/api/auth/login", json={"user_id": uid, "password": PASSWORD})
        if r.status_code != 200:
            return (user_index, f"login {r.status_code}")
        r = client.post(
            "/api/cscl/scripts",
            json={"title": f"Load script {user_index}", "topic": f"Topic {user_index}", "course_id": course_id},
        )
        if r.status_code not in (200, 201):
            return (user_index, f"create_script {r.status_code}")
        r = client.post(
            f"/api/cscl/courses/{course_id}/docs/upload",
            data={"title": filename, "file": (BytesIO(file_bytes), filename, mime_type)},
        )
        if r.status_code not in (200, 201):
            return (user_index, f"upload {r.status_code} {r.get_data(as_text=True)[:200]}")
        body = r.get_json()
        if body.get("error") or body.get("code") in ("PDF_PARSE_FAILED", "UNSUPPORTED_FILE_TYPE", "TEXT_TOO_SHORT"):
            return (user_index, f"upload error {body.get('error')} code={body.get('code')}")
        doc = body.get("document") or body.get("doc")
        if not doc:
            return (user_index, "no document in response")
        full_text = body.get("extracted_text") or body.get("extracted_text_preview") or ""
        marker = f"DEMO-{user_index:02d}"
        if marker not in full_text:
            return (user_index, f"content mismatch (marker {marker} not in extracted text)")
        r = client.get(f"/api/cscl/courses/{course_id}/docs")
        if r.status_code != 200:
            return (user_index, f"list_docs {r.status_code}")
        list_body = r.get_json()
        docs = list_body.get("documents") if isinstance(list_body, dict) else list_body
        if not isinstance(docs, list) or not any(d.get("id") == doc.get("id") for d in docs):
            return (user_index, "list_docs missing uploaded doc")
    return (user_index, None)


@pytest.fixture(scope="module")
def app_concurrent():
    """App with file-based SQLite so all threads share the same DB."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite:///{path}"
    app_instance = _create_app(url)
    yield app_instance
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture(scope="module")
def db_setup_concurrent(app_concurrent):
    from app.db import db
    from app.models import User, UserRole
    with app_concurrent.app_context():
        db.create_all()
        for i in range(1, NUM_USERS + 1):
            uid = f"teacher_load_{i}"
            u = db.session.get(User, uid)
            if u is None:
                u = User(id=uid, role=UserRole.TEACHER, created_at=datetime.utcnow())
                u.set_password(PASSWORD)
                db.session.add(u)
        db.session.commit()
    yield
    with app_concurrent.app_context():
        db.session.remove()
        db.drop_all()


def test_20_users_upload_concurrent(app_concurrent, db_setup_concurrent):
    """20 users upload different demo files concurrently (thread pool) to expose race conditions.
    Skipped on SQLite (multi-thread can raise ValueError/InterfaceError). Use PostgreSQL or
    scripts/load_test_20_users.py for reliable concurrent testing.
    """
    if "sqlite" in (app_concurrent.config.get("DATABASE_URL") or ""):
        pytest.skip("Concurrent upload test skipped on SQLite; use PostgreSQL or scripts/load_test_20_users.py")
    demo_files = get_demo_files()
    assert len(demo_files) == NUM_USERS
    errors = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {
            ex.submit(
                _run_one_user_upload,
                app_concurrent,
                user_index,
                filename,
                file_bytes,
                mime_type,
            ): user_index
            for (user_index, filename, file_bytes, mime_type) in demo_files
        }
        for fut in as_completed(futures):
            user_index, err = fut.result()
            if err:
                errors.append(f"User {user_index}: {err}")
    assert not errors, "Errors:\n" + "\n".join(errors)
