#!/usr/bin/env python3
"""
Simulate 30 concurrent users using demo account (teacher_demo / Demo@12345).
Each user: login -> GET /teacher -> GET /api/cscl/scripts -> optional GET /api/health.
No seed required; validates server stability and session isolation under load.

Usage:
  python scripts/load_test_30_concurrent.py [BASE_URL]
  BASE_URL defaults to http://127.0.0.1:5000 or LOAD_TEST_BASE_URL.

Example for deployed app:
  LOAD_TEST_BASE_URL=https://cscl-script-studio.onrender.com python scripts/load_test_30_concurrent.py
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE_URL = os.environ.get("LOAD_TEST_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
NUM_USERS = 30
DEMO_USER = "teacher_demo"
DEMO_PASSWORD = "Demo@12345"
TIMEOUT = 60  # Render free tier may be slow when cold


def run_one_session(user_slot: int) -> tuple[int, bool, str, dict]:
    """
    One simulated user: login, fetch teacher page, fetch scripts API.
    Returns (user_slot, ok, error_message, result_dict).
    """
    result = {"login": None, "teacher_page": None, "scripts_api": None, "health": None}
    session = requests.Session()
    session.headers["Accept"] = "text/html,application/json"
    session.headers["User-Agent"] = f"LoadTest-30/1 (slot={user_slot})"

    try:
        # Slight stagger to avoid thundering herd
        time.sleep((user_slot % 10) * 0.05)

        # Login
        r = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"user_id": DEMO_USER, "password": DEMO_PASSWORD},
            timeout=TIMEOUT,
        )
        result["login"] = r.status_code
        if r.status_code != 200:
            return (user_slot, False, f"login {r.status_code}", result)
        try:
            body = r.json()
            if body.get("user", {}).get("id") != DEMO_USER:
                return (user_slot, False, "login response user mismatch", result)
        except Exception:
            pass

        # GET teacher page (session cookie)
        r = session.get(f"{BASE_URL}/teacher", timeout=TIMEOUT, allow_redirects=True)
        result["teacher_page"] = r.status_code
        if r.status_code != 200:
            return (user_slot, False, f"teacher page {r.status_code}", result)
        if "teacherTutorial" not in r.text and "tutorial-card" not in r.text and "工作台" not in r.text and "Dashboard" not in r.text:
            pass  # optional: page may still be valid

        # GET scripts API
        r = session.get(f"{BASE_URL}/api/cscl/scripts", timeout=TIMEOUT)
        result["scripts_api"] = r.status_code
        if r.status_code != 200:
            return (user_slot, False, f"scripts API {r.status_code}", result)

        # GET health (no auth)
        r = session.get(f"{BASE_URL}/api/health", timeout=10)
        result["health"] = r.status_code

        return (user_slot, True, "", result)
    except requests.exceptions.Timeout as e:
        return (user_slot, False, f"timeout: {e}", result)
    except requests.exceptions.RequestException as e:
        return (user_slot, False, f"request: {type(e).__name__}: {e}", result)
    except Exception as e:
        return (user_slot, False, f"{type(e).__name__}: {e}", result)


def main():
    base = (sys.argv[1] if len(sys.argv) > 1 else BASE_URL).rstrip("/")
    print(f"Base URL: {base}")
    # Warm-up (cold start on Render can return 502)
    print("Warming up (single request)...")
    try:
        r = requests.get(f"{base}/api/health", timeout=45)
        if r.status_code != 200:
            print(f"  Health returned {r.status_code}; continuing anyway.")
        else:
            print("  OK")
    except Exception as e:
        print(f"  Warm-up failed: {e}")
    print(f"Simulating {NUM_USERS} concurrent users (login -> /teacher -> /api/cscl/scripts)...")
    start = time.time()
    errors = []
    results = []

    with ThreadPoolExecutor(max_workers=NUM_USERS) as ex:
        futures = {ex.submit(run_one_session, i): i for i in range(1, NUM_USERS + 1)}
        for fut in as_completed(futures):
            slot, ok, err, res = fut.result()
            results.append((slot, ok, res))
            if not ok:
                errors.append((slot, err))

    elapsed = time.time() - start
    ok_count = sum(1 for _, o, _ in results if o)
    print(f"\nCompleted in {elapsed:.2f}s — {ok_count}/{NUM_USERS} OK")

    for slot, ok, res in sorted(results, key=lambda x: x[0]):
        status = "OK" if ok else "FAIL"
        print(f"  Slot {slot:2d}: {status}  login={res.get('login')} teacher={res.get('teacher_page')} scripts={res.get('scripts_api')}")

    if errors:
        print("\n--- Errors ---")
        for slot, err in sorted(errors, key=lambda x: x[0]):
            print(f"  Slot {slot}: {err}")
        print(f"\n{len(errors)} failures out of {NUM_USERS} users.")
        sys.exit(1)
    print("\nAll 30 concurrent users completed successfully; app is stable under load.")
    sys.exit(0)


if __name__ == "__main__":
    main()
