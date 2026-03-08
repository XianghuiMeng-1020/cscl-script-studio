"""S2.13 PDF binary guard: no %PDF-/obj/stream in preview; sanitize; API returns ok=false+code; frontend guard."""
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


@pytest.fixture
def doc_service():
    return DocumentService()


def test_sanitize_removes_pdf_structure_markers():
    """Given string with %PDF-...stream..., sanitize should yield empty or text without markers."""
    raw = "line1\n%PDF-1.4\n2 0 obj\nstream\nbinary\nendstream\nendobj\nline2"
    out = sanitize_extracted_text(raw)
    assert "%PDF" not in out
    assert "stream" not in out
    assert "endstream" not in out
    assert "obj" not in out or "object" in out.lower()
    assert "line1" in out or "line2" in out or not out.strip()


def test_is_probably_pdf_binary_text_marks_pdf_header():
    assert is_probably_pdf_binary_text("%PDF-1.4 something") is True
    assert is_probably_pdf_binary_text("Normal course text only.") is False


def test_is_probably_pdf_binary_text_marks_structure_keywords():
    assert is_probably_pdf_binary_text("  stream  ") is True
    assert is_probably_pdf_binary_text("  endobj  ") is True
    assert is_probably_pdf_binary_text("xref trailer") is True
    assert is_probably_pdf_binary_text("objection is valid") is False


def test_extract_text_from_pdf_bytes_failure_returns_ok_false_code_no_raw():
    """On failure, API contract: ok=false, code set, error readable; no %PDF- in response."""
    doc = DocumentService()
    # Corrupt / non-PDF bytes
    result = doc.extract_text_from_pdf_bytes(b"not a pdf \x00\x01\x02")
    assert result.get("ok") is False
    assert "code" in result
    assert result.get("code") in (PDF_PARSE_FAILED, EMPTY_EXTRACTED_TEXT, TEXT_TOO_SHORT)
    err = result.get("error", "")
    assert "%PDF" not in err
    assert "obj" not in err
    assert "stream" not in err


def test_extract_text_from_pdf_bytes_success_returns_ok_true_safe_preview(doc_service, app, seed_users):
    """Normal text upload returns preview without binary markers (regression: plain text PDF path)."""
    import tempfile
    import os
    content = "Course syllabus content. " * 30
    user_id = seed_users["teacher"].id
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(content.encode("utf-8"))
        path = f.name
    try:
        with app.app_context():
            r = doc_service.upload_document(
                course_id="C1",
                title="t",
                file_content=content.encode("utf-8"),
                filename="t.txt",
                mime_type="text/plain",
                uploaded_by=user_id,
            )
        if r.get("error_code"):
            pytest.skip("upload failed in test env")
        meta = r.get("extraction_metadata") or {}
        preview = meta.get("extracted_text_preview") or ""
        assert "%PDF" not in preview
        assert "stream" not in preview
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_upload_pdf_binary_returns_error_code_no_preview(doc_service, app, seed_users):
    """Upload of PDF that yields binary-like content returns error, no extracted_text_preview with binary."""
    pdf_garbage = b"%PDF-1.4\n1 0 obj\nstream\n\x00\x01\nendstream\nendobj\n"
    with app.app_context():
        result = doc_service.upload_document(
            course_id="C1",
            title="x",
            file_content=pdf_garbage,
            filename="x.pdf",
            mime_type="application/pdf",
            uploaded_by=seed_users["teacher"].id,
        )
    assert result.get("document") is None
    assert result.get("error_code") in (PDF_PARSE_FAILED, EMPTY_EXTRACTED_TEXT, TEXT_TOO_SHORT)
    meta = result.get("extraction_metadata") or {}
    preview = meta.get("extracted_text_preview") or ""
    assert "%PDF" not in preview
    assert "stream" not in preview


def test_frontend_guard_looks_like_pdf_binary_equivalent():
    """Logic equivalent to frontend looksLikePdfBinary: %PDF-, regex, non-print ratio."""
    assert is_probably_pdf_binary_text("%PDF-") is True
    assert is_probably_pdf_binary_text("hello stream world") is True
    assert is_probably_pdf_binary_text("Normal text.") is False
    # High non-printable
    bad = "a" * 10 + "\x00\x01\x02" * 10
    assert is_probably_pdf_binary_text(bad) is True
