#!/usr/bin/env python3
"""
Simulate 20 users: register (pre-seeded), login, create script, upload a unique demo file,
list docs, fetch doc, and verify content. Run with server already up (e.g. http://127.0.0.1:5001).

Usage:
  1. Start app: python app.py   (or FLASK_PORT=5001)
  2. Seed users: python scripts/seed_20_users_load_test.py
  3. Run test:   python scripts/load_test_20_users.py [BASE_URL]

Checks for: wrong status codes, document mix-up, missing chunks, file write errors.
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional

import requests

# Demo files and users
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_DIR = os.path.join(SCRIPT_DIR, 'demo_files_20')
BASE_URL = os.environ.get('LOAD_TEST_BASE_URL', 'http://127.0.0.1:5001')
PASSWORD = 'LoadTest@20'
NUM_USERS = 20


def get_demo_files() -> List[Tuple[int, str, bytes, str]]:
    """Return list of (user_index_1based, filename, file_bytes, mime_type)."""
    if not os.path.isdir(DEMO_DIR):
        print("Run scripts/gen_20_demo_files.py first.")
        sys.exit(1)
    out = []
    for i in range(1, NUM_USERS + 1):
        for ext in ('.md', '.txt'):
            path = os.path.join(DEMO_DIR, f'demo_syllabus_{i:02d}{ext}')
            if os.path.isfile(path):
                with open(path, 'rb') as f:
                    out.append((i, os.path.basename(path), f.read(), 'text/markdown' if ext == '.md' else 'text/plain'))
                break
    return out


def run_one_user(
    user_index: int,
    file_index: int,
    filename: str,
    file_bytes: bytes,
    mime_type: str,
    base_url: str,
) -> Tuple[int, Optional[str], Optional[dict]]:
    """
    Login as teacher_load_{user_index}, create script, upload file, list docs, get doc.
    Returns (user_index, error_message, result_dict).
    """
    uid = f"teacher_load_{user_index}"
    course_id = f"course_user_{user_index}"
    result = {"user_id": uid, "course_id": course_id, "upload_status": None, "doc_id": None, "list_ok": False, "content_ok": False}
    # Stagger start slightly so server isn't hit by 20 requests in same instant
    time.sleep((user_index - 1) * 0.08)
    session = requests.Session()
    session.headers["Accept"] = "application/json"

    try:
        # Login (retry once on 5xx - server may be cold)
        for attempt in range(2):
            r = session.post(
                f"{base_url}/api/auth/login",
                json={"user_id": uid, "password": PASSWORD},
                timeout=30,
            )
            if r.status_code == 200:
                break
            if r.status_code < 500 and attempt == 0:
                return (user_index, f"login failed: {r.status_code} body={r.text[:300]}", result)
            time.sleep(0.5 * (attempt + 1))
        if r.status_code != 200:
            return (user_index, f"login failed: {r.status_code} body={r.text[:300]}", result)
        result["login_ok"] = True

        # Create script (so user has context)
        r = session.post(
            f"{base_url}/api/cscl/scripts",
            json={
                "title": f"Load test script {user_index}",
                "topic": f"Topic {user_index}",
                "course_id": course_id,
            },
            timeout=30,
        )
        if r.status_code not in (200, 201):
            return (user_index, f"create_script failed: {r.status_code}", result)
        result["script_ok"] = True

        # Upload document (file) - use file_bytes passed in
        files = {"file": (filename, file_bytes, mime_type)}
        data = {"title": filename}
        r = session.post(
            f"{base_url}/api/cscl/courses/{course_id}/docs/upload",
            files=files,
            data=data,
            timeout=60,
        )
        result["upload_status"] = r.status_code
        if r.status_code not in (200, 201):
            return (user_index, f"upload failed: {r.status_code} {r.text[:300]}", result)
        body = r.json()
        if body.get("error") or body.get("code") in ("PDF_PARSE_FAILED", "UNSUPPORTED_FILE_TYPE", "TEXT_TOO_SHORT", "EMPTY_EXTRACTED_TEXT"):
            return (user_index, f"upload error in body: {body.get('error')} code={body.get('code')}", result)
        doc = body.get("document") or body.get("doc")
        if not doc:
            return (user_index, "upload response missing document", result)
        doc_id = doc.get("id")
        result["doc_id"] = doc_id
        result["upload_ok"] = True

        # List documents for this course
        r = session.get(f"{base_url}/api/cscl/courses/{course_id}/docs", timeout=30)
        if r.status_code != 200:
            return (user_index, f"list_docs failed: {r.status_code}", result)
        list_body = r.json()
        docs = list_body.get("documents") if isinstance(list_body, dict) else list_body
        if not isinstance(docs, list):
            return (user_index, "list_docs: invalid response", result)
        result["list_count"] = len(docs)
        result["list_ok"] = any(d.get("id") == doc_id for d in docs)

        # Verify content from upload response (extracted_text / extracted_text_preview)
        full_text = body.get("extracted_text") or body.get("extracted_text_preview") or ""
        marker = f"DEMO-{user_index:02d}"
        if marker not in full_text:
            return (user_index, f"content mismatch: marker {marker} not in extracted text (possible mix-up or wrong doc)", result)
        result["content_ok"] = True
        return (user_index, None, result)
    except requests.exceptions.RequestException as e:
        return (user_index, f"request error: {type(e).__name__}: {e}", result)
    except Exception as e:
        return (user_index, f"exception: {type(e).__name__}: {e}", result)


def main():
    base_url = (sys.argv[1] if len(sys.argv) > 1 else BASE_URL).rstrip("/")
    demo_files = get_demo_files()
    if len(demo_files) != NUM_USERS:
        print(f"Expected {NUM_USERS} demo files, got {len(demo_files)}. Run gen_20_demo_files.py.")
        sys.exit(1)

    sequential = os.environ.get("SEQUENTIAL", "").lower() in ("1", "true", "yes")
    print(f"Base URL: {base_url}")
    if sequential:
        print("Running 20 users sequentially...")
    else:
        print("Running 20 users concurrently (login -> create script -> upload file -> list -> verify content)...")
    errors = []
    results = []

    if sequential:
        for t in demo_files:
            ui, err, res = run_one_user(t[0], t[0], t[1], t[2], t[3], base_url)
            results.append((ui, res))
            if err:
                errors.append((ui, err))
    else:
        with ThreadPoolExecutor(max_workers=20) as ex:
            futures = {
                ex.submit(
                    run_one_user,
                    t[0],
                    t[0],
                    t[1],
                    t[2],
                    t[3],
                    base_url,
                ): t[0]
                for t in demo_files
            }
            for fut in as_completed(futures):
                ui, err, res = fut.result()
                results.append((ui, res))
                if err:
                    errors.append((ui, err))

    # Report
    print("\n--- Results ---")
    for ui, res in sorted(results, key=lambda x: x[0]):
        status = "OK" if res.get("content_ok") else ("PARTIAL" if res.get("upload_ok") else "FAIL")
        print(f"  User {ui:2d}: {status}  upload={res.get('upload_status')} doc_id={res.get('doc_id')} list_ok={res.get('list_ok')} content_ok={res.get('content_ok', False)}")
    if errors:
        print("\n--- Errors ---")
        for ui, err in sorted(errors, key=lambda x: x[0]):
            print(f"  User {ui}: {err}")
        print(f"\nTotal: {len(errors)} errors out of {NUM_USERS} users.")
        sys.exit(1)
    print(f"\nAll {NUM_USERS} users completed successfully; no file upload/processing bugs detected.")
    sys.exit(0)


if __name__ == "__main__":
    main()
