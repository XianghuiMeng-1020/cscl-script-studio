"""C2 / B3: 413 FILE_TOO_LARGE and unified error body (success, error_code, message, trace_id)."""
import pytest
import json
from io import BytesIO


def test_upload_file_too_large_returns_413_and_unified_json(client, app, seed_users):
    """Upload with content over size limit returns 413 and strict JSON shape."""
    app.config['DOCUMENT_MAX_FILE_SIZE_MB'] = 0.0001  # ~100 bytes
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    # Simulate file upload: 200 bytes (no content_type so client sets multipart boundary)
    payload = {'file': (BytesIO(b'x' * 200), 'big.pdf'), 'title': 'Big'}
    resp = client.post(
        '/api/cscl/courses/default-course/docs/upload',
        data=payload,
    )
    assert resp.status_code == 413, resp.data
    body = json.loads(resp.data)
    assert body.get('success') is False
    assert body.get('error_code') == 'FILE_TOO_LARGE'
    assert 'message' in body
    assert 'trace_id' in body
    assert body.get('details', {}).get('max_size_mb') is not None


def test_api_404_returns_trace_id(client, app):
    """API 404 response includes trace_id."""
    resp = client.get('/api/nonexistent-resource-404')
    assert resp.status_code == 404
    body = json.loads(resp.data)
    assert 'trace_id' in body
    assert body.get('error_code') == 'NOT_FOUND'


def test_api_response_includes_x_request_id_header(client, app):
    """C2: Successful API response includes X-Request-Id header."""
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert 'X-Request-Id' in resp.headers
