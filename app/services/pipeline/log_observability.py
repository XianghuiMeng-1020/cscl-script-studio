"""Structured JSON-line logging for pipeline stages (grep-able in docker compose logs)."""
import json
import logging
import sys
from typing import Optional

_log = logging.getLogger(__name__)


def log_stage_stdout(
    run_id: str,
    stage_name: str,
    provider: str,
    model: str,
    latency_ms: int,
    success: bool,
    error_type: Optional[str],
) -> None:
    payload = {
        "run_id": run_id,
        "stage_name": stage_name,
        "provider": provider,
        "model": model,
        "latency_ms": latency_ms,
        "success": bool(success),
        "error_type": error_type,
    }
    line = json.dumps(payload, ensure_ascii=False)
    sys.stderr.write(f"PIPELINE_STAGE_JSON {line}\n")
    sys.stderr.flush()
    _log.info("PIPELINE_STAGE_JSON %s", line)
