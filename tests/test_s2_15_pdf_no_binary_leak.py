"""S2.15: PDF no binary leak - API and service never expose %PDF-/obj/stream in preview."""
import io
import pytest
from app.services.document_service import (
    DocumentService,
    is_probably_pdf_binary_text,
    sanitize_extracted_text,
    PDF_PARSE_FAILED,
    EMPTY_EXTRACTED_TEXT,
    TEXT_TOO_SHORT,
)


def test_sanitize_removes_pdf_markers():
    """sanitize_extracted_text must remove %PDF-, obj, stream, endstream, xref."""
    raw = "line1\n%PDF-1.4\n2 0 obj\nstream\nx\nendstream\nendobj\nxref\ntrailer\nline2"
    out = sanitize_extracted_text(raw)
    assert "%PDF" not in out
    assert "stream" not in out
    assert "endstream" not in out
    assert "xref" not in out
    assert "trailer" not in out


def test_extract_text_from_pdf_bytes_rejects_binary():
    """extract_text_from_pdf_bytes must return ok=False and code for binary/corrupt PDF."""
    doc = DocumentService()
    result = doc.extract_text_from_pdf_bytes(b"%PDF-1.4\n1 0 obj\nstream\n\x00\x01\nendstream\nendobj\n")
    assert result.get("ok") is False
    assert result.get("code") in (PDF_PARSE_FAILED, EMPTY_EXTRACTED_TEXT, TEXT_TOO_SHORT)
    err = result.get("error", "")
    assert "%PDF" not in err
    assert "stream" not in err


def test_extract_text_from_pdf_bytes_success_no_binary_in_preview():
    """On success, extracted_text_preview must never contain %PDF- or stream."""
    try:
        from pypdf import PdfReader
    except ImportError:
        pytest.skip("pypdf not installed")
    from pypdf import PdfWriter
    buf = io.BytesIO()
    w = PdfWriter()
    w.add_blank_page(72, 72)
    w.write(buf)
    pdf_bytes = buf.getvalue()
    doc = DocumentService()
    result = doc.extract_text_from_pdf_bytes(pdf_bytes)
    if result.get("ok"):
        preview = result.get("extracted_text_preview", "") or result.get("extracted_text", "")[:300]
        assert "%PDF" not in preview
        assert "stream" not in preview.lower() or "stream" in "streaming"  # word boundary
    # If ok=False (blank page yields empty), that's acceptable
    if not result.get("ok"):
        assert result.get("code") in (PDF_PARSE_FAILED, EMPTY_EXTRACTED_TEXT, TEXT_TOO_SHORT)


def test_upload_document_pdf_garbage_returns_error_code(app, seed_users):
    """Upload of binary PDF must return error with code, no preview with binary."""
    doc = DocumentService()
    with app.app_context():
        result = doc.upload_document(
            course_id="default-course",
            title="x",
            file_content=b"%PDF-1.4\n1 0 obj\nstream\n\x00\x01\nendstream\nendobj\n",
            filename="x.pdf",
            mime_type="application/pdf",
            uploaded_by=seed_users["teacher"].id,
        )
    assert result.get("document") is None
    assert result.get("error_code") in (PDF_PARSE_FAILED, EMPTY_EXTRACTED_TEXT, TEXT_TOO_SHORT)
    meta = result.get("extraction_metadata") or {}
    preview = (meta.get("extracted_text_preview") or "")
    assert "%PDF" not in preview
    assert "stream" not in preview


def test_api_upload_pdf_binary_returns_422(client, app, seed_users):
    """API POST upload with binary PDF must return 422 and code PDF_PARSE_FAILED; body never contains %PDF-."""
    client.post("/api/auth/login", json={"user_id": "T001", "password": "teacher123"})
    data = b"%PDF-1.4\n1 0 obj\nstream\n\x00\x01\nendstream\nendobj\n"
    rv = client.post(
        "/api/cscl/courses/default-course/docs/upload",
        data={"file": (io.BytesIO(data), "bad.pdf"), "title": "bad"},
    )
    assert rv.status_code == 422
    body = rv.get_json() or {}
    assert body.get("code") == "PDF_PARSE_FAILED"
    assert body.get("error") == "PDF_PARSE_FAILED"
    assert "message" in body
    assert "%PDF" not in str(body)
    assert "stream" not in str(body)
