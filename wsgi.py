"""
WSGI entry point for Gunicorn
"""
import sys
import os
import logging

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("wsgi")

logger.info("Python %s | cwd=%s | PORT=%s", sys.version, os.getcwd(), os.environ.get("PORT", "(unset)"))

try:
    from app import create_app
    application = create_app()
    app = application
    logger.info("Flask app created successfully")
except Exception:
    logger.exception("FATAL: Flask app failed to start")
    raise

if __name__ == '__main__':
    application.run()
