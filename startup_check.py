"""Pre-flight check: validate that the Flask app can be imported and created."""
import sys
import os
import traceback

print(f"=== STARTUP CHECK ===", flush=True)
print(f"Python: {sys.version}", flush=True)
print(f"CWD: {os.getcwd()}", flush=True)
print(f"PORT: {os.environ.get('PORT', '(not set)')}", flush=True)
print(f"OPENAI_API_KEY set: {bool(os.environ.get('OPENAI_API_KEY'))}", flush=True)
print(f"SECRET_KEY set: {bool(os.environ.get('SECRET_KEY'))}", flush=True)
print(f"LLM_PROVIDER: {os.environ.get('LLM_PROVIDER', '(not set)')}", flush=True)

os.makedirs('data/course_documents', exist_ok=True)
print("data/course_documents directory: OK", flush=True)

try:
    from app import create_app
    app = create_app()
    print(f"Flask app created OK – {len(list(app.url_map.iter_rules()))} routes", flush=True)
except Exception:
    traceback.print_exc()
    print("FATAL: Flask app creation failed", flush=True)
    sys.exit(1)

print("=== STARTUP CHECK PASSED ===", flush=True)
