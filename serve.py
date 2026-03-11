"""Minimal server for Railway debugging - bypasses gunicorn."""
import os
import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("serve")

os.makedirs("data/course_documents", exist_ok=True)

port = int(os.environ.get("PORT", 8080))
log.info("Starting Flask dev server on 0.0.0.0:%d", port)

from app import create_app
app = create_app()
log.info("App created, %d routes", len(list(app.url_map.iter_rules())))
app.run(host="0.0.0.0", port=port, debug=False)
