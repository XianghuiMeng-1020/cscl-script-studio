"""Production-ready server for Railway using waitress (or Flask fallback)."""
import os
import sys
import subprocess
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("serve")

os.makedirs("data/course_documents", exist_ok=True)

# Run migrations on startup (e.g. Railway deploy)
if os.environ.get("RUN_MIGRATIONS", "1") == "1":
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            log.info("Migrations applied successfully")
        else:
            log.warning("Migration exit code %s: %s", result.returncode, result.stderr or result.stdout)
    except Exception as e:
        log.warning("Migration run failed (continuing): %s", e)

port = int(os.environ.get("PORT", 8080))

from app import create_app
app = create_app()
log.info("App created with %d routes", len(list(app.url_map.iter_rules())))

try:
    from waitress import serve
    log.info("Starting waitress on 0.0.0.0:%d", port)
    serve(app, host="0.0.0.0", port=port, threads=4, channel_timeout=300)
except ImportError:
    log.warning("waitress not installed, falling back to Flask dev server")
    app.run(host="0.0.0.0", port=port, debug=False)
