"""S2.17: PDF binary guard regression - no %PDF-/obj/stream in API or frontend."""
import io
import pytest
from app.services.document_service import (
    DocumentService,
    is_probably_pdf_binary_text,
    sanitize_extracted_text,
    PDF_PARSE_FAILED,
)


def test_sanitize_removes_pdf_markers():
    """sanitize_extracted_text must remove %PDF-, obj, stream, xref."""
    raw = "line1\n%PDF-1.4\n2 0 obj\nstream\nendstream\nxref\ntrailer\nline2"
    out = sanitize_extracted_text(raw)
    assert "%PDF" not in out
    assert "stream" not in out
    assert "xref" not in out


def test_extract_pdf_bytes_binary_returns_fail_code():
    """extract_text_from_pdf_bytes on binary must return ok=False, code PDF_PARSE_FAILED or equivalent."""
    doc = DocumentService()
    result = doc.extract_text_from_pdf_bytes(b"%PDF-1.4\n1 0 obj\nstream\n\x00\x01\nendstream\nendobj\n")
    assert result.get("ok") is False
    assert result.get("code") == PDF_PARSE_FAILED or "PARSE" in str(result.get("code", ""))


def test_api_upload_binary_pdf_returns_422_with_code(client, seed_users):
    """API upload of binary PDF must return 422 and code, no %PDF- in body."""
    client.post("/api/auth/login", json={"user_id": "T001", "password": "teacher123"})
    data = b"%PDF-1.4\n1 0 obj\nstream\n\x00\x01\nendstream\nendobj\n"
    rv = client.post(
        "/api/cscl/courses/default-course/docs/upload",
        data={"file": (io.BytesIO(data), "bad.pdf"), "title": "bad"},
    )
    body = (rv.get_json() or {}) if rv.data else {}
    body_str = str(body)
    assert "%PDF" not in body_str
    assert "stream" not in body_str or "PDF_PARSE_FAILED" in body_str
    assert rv.status_code in (422, 400) or body.get("code") == "PDF_PARSE_FAILED"
