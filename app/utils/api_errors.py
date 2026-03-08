"""B3: Unified API error response shape. All API routes should return JSON only."""
from typing import Any, Dict, Optional, Tuple
from flask import jsonify, request, g
import uuid


def _get_trace_id() -> str:
    """Use g.request_id if set (e.g. by middleware), else generate one."""
    if g and getattr(g, 'request_id', None):
        return str(g.request_id)
    return str(uuid.uuid4())[:16]


def api_error(
    error_code: str,
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
) -> Tuple[Dict[str, Any], int]:
    """
    Build standard API error body and status code.
    Shape: { success: false, error_code, message, details?, trace_id? }
    Returns (dict, status_code) for jsonify(...), status_code.
    """
    body = {
        'success': False,
        'error_code': error_code,
        'message': message,
    }
    if details is not None:
        body['details'] = details
    body['trace_id'] = trace_id or _get_trace_id()
    return body, status_code


def api_error_response(
    error_code: str,
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
):
    """Return (Flask response, status_code) for API errors."""
    body, code = api_error(error_code, message, status_code, details, trace_id)
    return jsonify(body), code


def is_api_request() -> bool:
    """True if current request path is under /api/."""
    return request.path.startswith('/api/') if request else False
