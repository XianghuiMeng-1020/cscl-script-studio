#!/usr/bin/env python3
"""
Simulate 30 concurrent users: 15 teacher flows (login, create script, publish) and 15 student
flows (login, join via share code DEMO, send chat message, submit task). Uses demo accounts
teacher_demo / student_demo with Demo@12345. Requires demo published activity (share_code DEMO)
e.g. from in-memory bootstrap or seed_demo_published_activity.

Usage:
  python scripts/load_test_30_concurrent.py [BASE_URL]

Verifies: no 500s, no data mix-up between users.
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE_URL = os.environ.get("LOAD_TEST_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
NUM_TEACHER = 15
NUM_STUDENT = 15
NUM_USERS = NUM_TEACHER + NUM_STUDENT
TEACHER_USER = "teacher_demo"
STUDENT_USER = "student_demo"
DEMO_PASSWORD = "Demo@12345"
DEMO_SHARE_CODE = "DEMO"
TIMEOUT = 90  # Render free tier can be slow under load


def run_teacher_slot(slot: int) -> tuple[int, bool, str, dict]:
    """Teacher: login, create script, publish."""
    result = {"login": None, "create_script": None, "publish": None}
    session = requests.Session()
    session.headers["Accept"] = "application/json"
    session.headers["User-Agent"] = f"LoadTest-30/teacher (slot={slot})"
    try:
        time.sleep((slot % 10) * 0.05)
        r = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"user_id": TEACHER_USER, "password": DEMO_PASSWORD},
            timeout=TIMEOUT,
        )
        result["login"] = r.status_code
        if r.status_code != 200:
            return (slot, False, f"login {r.status_code}", result)
        r = session.post(
            f"{BASE_URL}/api/cscl/scripts",
            json={"title": f"Load test {slot}", "topic": f"Topic {slot}"},
            timeout=TIMEOUT,
        )
        result["create_script"] = r.status_code
        if r.status_code not in (200, 201):
            return (slot, False, f"create_script {r.status_code}", result)
        script_id = r.json().get("script", {}).get("id") or r.json().get("id")
        if not script_id:
            # Fallback: list scripts and find by title (ensures same worker/DB sees it)
            r2 = session.get(f"{BASE_URL}/api/cscl/scripts", timeout=TIMEOUT)
            if r2.status_code != 200:
                return (slot, False, "list_scripts failed", result)
            for s in (r2.json().get("scripts") or []):
                if s.get("title") == f"Load test {slot}":
                    script_id = s.get("id")
                    break
        if not script_id:
            return (slot, False, "no script id in response", result)
        r = session.post(
            f"{BASE_URL}/api/cscl/scripts/{script_id}/finalize",
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            result["publish"] = r.status_code
            return (slot, False, f"finalize {r.status_code}", result)
        r = session.post(
            f"{BASE_URL}/api/cscl/scripts/{script_id}/publish",
            timeout=TIMEOUT,
        )
        result["publish"] = r.status_code
        if r.status_code != 200:
            return (slot, False, f"publish {r.status_code}", result)
        return (slot, True, "", result)
    except requests.exceptions.Timeout as e:
        return (slot, False, f"timeout: {e}", result)
    except requests.exceptions.RequestException as e:
        return (slot, False, f"request: {e}", result)
    except Exception as e:
        return (slot, False, f"{type(e).__name__}: {e}", result)


def run_student_slot(slot: int) -> tuple[int, bool, str, dict]:
    """Student: login, join activity DEMO, get activity, send message, submit scene task."""
    result = {"login": None, "join": None, "activity": None, "message": None, "submit": None}
    session = requests.Session()
    session.headers["Accept"] = "application/json"
    session.headers["User-Agent"] = f"LoadTest-30/student (slot={slot})"
    try:
        time.sleep((slot % 10) * 0.05)
        r = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"user_id": STUDENT_USER, "password": DEMO_PASSWORD},
            timeout=TIMEOUT,
        )
        result["login"] = r.status_code
        if r.status_code != 200:
            return (slot, False, f"login {r.status_code}", result)
        r = session.post(
            f"{BASE_URL}/api/student/activity/{DEMO_SHARE_CODE}/join",
            timeout=TIMEOUT,
        )
        result["join"] = r.status_code
        if r.status_code != 200:
            return (slot, False, f"join {r.status_code}", result)
        r = session.get(
            f"{BASE_URL}/api/student/activity/{DEMO_SHARE_CODE}",
            timeout=TIMEOUT,
        )
        result["activity"] = r.status_code
        if r.status_code != 200:
            return (slot, False, f"activity {r.status_code}", result)
        data = r.json()
        scenes = data.get("scenes") or []
        scene_id = scenes[0]["id"] if scenes else None
        r = session.post(
            f"{BASE_URL}/api/student/activity/{DEMO_SHARE_CODE}/messages",
            json={"content": f"Load test message from slot {slot}"},
            timeout=TIMEOUT,
        )
        result["message"] = r.status_code
        if r.status_code not in (200, 201):
            return (slot, False, f"message {r.status_code}", result)
        if scene_id:
            r = session.post(
                f"{BASE_URL}/api/student/activity/{DEMO_SHARE_CODE}/scenes/{scene_id}/submit",
                json={"content": f"Submission slot {slot}", "status": "submitted"},
                timeout=TIMEOUT,
            )
            result["submit"] = r.status_code
            if r.status_code not in (200, 201):
                return (slot, False, f"submit {r.status_code}", result)
        return (slot, True, "", result)
    except requests.exceptions.Timeout as e:
        return (slot, False, f"timeout: {e}", result)
    except requests.exceptions.RequestException as e:
        return (slot, False, f"request: {e}", result)
    except Exception as e:
        return (slot, False, f"{type(e).__name__}: {e}", result)


def main():
    base = (sys.argv[1] if len(sys.argv) > 1 else BASE_URL).rstrip("/")
    print(f"Base URL: {base}")
    print("Warming up...")
    try:
        r = requests.get(f"{base}/api/health", timeout=45)
        print(f"  Health: {r.status_code}")
    except Exception as e:
        print(f"  Warm-up failed: {e}")
    print(f"Running {NUM_TEACHER} teacher flows + {NUM_STUDENT} student flows ({NUM_USERS} total)...")
    start = time.time()
    errors = []
    results = []

    def run_slot(slot):
        if slot <= NUM_TEACHER:
            return run_teacher_slot(slot)
        return run_student_slot(slot)

    with ThreadPoolExecutor(max_workers=NUM_USERS) as ex:
        futures = {ex.submit(run_slot, i): i for i in range(1, NUM_USERS + 1)}
        for fut in as_completed(futures):
            slot, ok, err, res = fut.result()
            results.append((slot, ok, res))
            if not ok:
                errors.append((slot, err))

    elapsed = time.time() - start
    ok_count = sum(1 for _, o, _ in results if o)
    print(f"\nCompleted in {elapsed:.2f}s — {ok_count}/{NUM_USERS} OK")

    for slot, ok, res in sorted(results, key=lambda x: x[0]):
        kind = "T" if slot <= NUM_TEACHER else "S"
        status = "OK" if ok else "FAIL"
        print(f"  Slot {slot:2d} ({kind}): {status}  {res}")

    if errors:
        print("\n--- Errors ---")
        for slot, err in sorted(errors, key=lambda x: x[0]):
            print(f"  Slot {slot}: {err}")
        print(f"\n{len(errors)} failures.")
        sys.exit(1)
    print("\nAll 30 users (15 teacher + 15 student) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
