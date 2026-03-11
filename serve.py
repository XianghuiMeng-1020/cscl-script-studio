"""Production-ready server for Railway using waitress (or Flask fallback)."""
import os
import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("serve")

os.makedirs("data/course_documents", exist_ok=True)

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
