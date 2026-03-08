# Production Gap Report — Teacher-in-Loop CSCL

**Phase A: Discovery + Gap Analysis**  
**Date:** 2026-02-09  
**Baseline (do not break):** GET /api/health, POST /api/auth/login (teacher_demo), POST/GET /api/cscl/courses/<course_id>/docs/upload and /docs, PDF extraction returns clean `extracted_text_preview` (no binary in JSON), leak scan passed. `/api/teacher/documents/*` is not active and must not be reintroduced.

---

## 1. Inspection Summary

### 1.1 Route Map (Active Routes)

| Prefix | Source | Key routes |
|--------|--------|------------|
| **/api/health** | `app/routes/api.py` | GET — health + db + LLM status |
| **/api/auth** | `app/routes/auth.py` | POST /login, POST /logout, GET /me |
| **/api/cscl** | `app/routes/cscl.py` | **Canonical doc API:** POST/GET `/courses/<course_id>/docs/upload`, GET `/courses/<course_id>/docs`, DELETE `/courses/<course_id>/docs/<doc_id>`. Also: /spec/validate, /task-types, /scripts (CRUD), /scripts/…/generate-ai, regenerate-scene, revisions, decisions, decision-summary, decision-timeline/export, quality-report, **/scripts/…/pipeline/run**, GET /pipeline/runs/<run_id>, GET /scripts/…/pipeline/runs |
| **/api** | `app/routes/api.py` | assignments, rubrics, submissions, ai/*, engagement, logs, config, stats, users, demo/init, demo/scripts |
| **/**, **/login**, **/teacher**, **/demo** | `app/routes/teacher.py` | HTML pages (teacher dashboard, login, demo) |

No `/api/teacher/documents/*` routes exist; document operations use **/api/cscl/courses/<course_id>/docs/** only.

### 1.2 Upload / Extraction Service Flow

- **Entry:** `POST /api/cscl/courses/<course_id>/docs/upload` (file in `request.files['file']` or JSON `title`+`text`).
- **Service:** `DocumentService.upload_document()` (or `upload_text_document()`).
  - **Validation:** `allowed_file()` (extension: txt, md, pdf), `MAX_FILE_SIZE` (10MB), MIME not re-validated against extension.
  - **Dedup:** Same `checksum` + `course_id` → returns existing document (reuse); no versioning.
  - **PDF path:** `extract_text_from_pdf_bytes()` → pypdf page text only, no fallback extractor. Then `sanitize_extracted_text()`, `safe_preview_or_none()` before any response. No `page_count` in response.
  - **Storage:** File saved to `DATA_DIR/course_documents/{uuid}_{secure_filename}`; DB record + chunks in same `db.session.commit()`. Text docs have `storage_uri=None`.
- **Response:** 201 with `document`, `chunks_count`, `extraction_metadata` (detected_type, extracted_char_count, extraction_method, warnings, extracted_text_preview). Error responses use `error` + `code` (e.g. PDF_PARSE_FAILED, UNSUPPORTED_FILE_TYPE, TEXT_TOO_SHORT, EMPTY_EXTRACTED_TEXT); **FILE_TOO_LARGE** returns 400 with generic handler (no 413).

### 1.3 Frontend Pages (Upload / Form / Pipeline)

- **Teacher:** `templates/teacher.html` + `static/js/teacher.js`. Four-step flow: (1) Import syllabus, (2) Confirm objectives (spec form), (3) Generate (pipeline run), (4) Review & publish.
- **Step 1:** “导入课程大纲” — no inline upload in step 1; documents are in a separate “课程文档” view. Upload via `uploadDocument()`: file input, FormData to `POST .../courses/default-course/docs/upload`. **course_id is hardcoded `'default-course'`.**
- **Step 2:** Spec form (`specForm`): course (subject), topic, duration, mode, class_size, course_context (description), objectives, task_type, expected_output, collaboration_form, task_requirements. `buildCanonicalSpecFromForm()` builds `course_context`, `learning_objectives`, `task_requirements`. Validate → `POST /api/cscl/spec/validate`. On “Run pipeline”, script is created with `course_id: flat.course` (i.e. **course_context.subject**, e.g. “Introduction to Data Science”), so **script.course_id ≠ documents’ course_id** when docs are under `default-course`.
- **Step 3:** `POST /api/cscl/scripts/<id>/pipeline/run` with `{ spec: currentSpec }`. No preflight endpoint; provider readiness checked inside pipeline. Double-click can submit twice (no idempotency key).
- **Documents view:** `loadDocuments()` / `loadDocumentsView()` — GET `.../courses/default-course/docs`; list shows title, chunks_count, extracted_text_preview; no “use this doc to prefill” or link to spec.

### 1.4 Auto-Fill (Current vs Missing)

- **Current:** `fillSpecForm(spec)` exists and is used for **demo only**: sessionStorage `demoSpec` or hardcoded demo payload. Form fields are filled from that object (course, topic, duration, objectives, task_type, etc.).
- **Missing:** No prefill from **uploaded document text**. No endpoint such as `POST /api/cscl/courses/<course_id>/docs/<doc_id>/prefill` that returns structured fields (course_title, course_code, learning_outcomes, task_type, etc.) with confidence/source. Teacher always fills spec form manually (or via demo) before pipeline.

### 1.5 Known Fragile Points

- **course_id mismatch:** Documents under `default-course`; script created with `course_id = subject`. RAG uses `script.course_id` → no docs found for pipeline grounding when teacher uses default-course docs.
- **PDF:** Single extractor (pypdf); no fallback for sparse/image PDFs. No `page_count` in extraction metadata. Timeout: no explicit upload/PDF timeout; large PDF could hang.
- **Errors:** API error shape inconsistent (sometimes `error`+`code`, sometimes `valid`+`issues`); no standard `{ success: false, error_code, message, details?, trace_id? }`. FILE_TOO_LARGE not mapped to 413. No request_id/trace_id in responses.
- **Storage:** `get_course_documents()` does not verify `storage_uri` file exists; text docs have `storage_uri=None`.
- **Pipeline:** No preflight API; no idempotency key for run creation; double-click creates two runs. LLM timeouts exist in provider (e.g. OPENAI_TIMEOUT_SECONDS, QWEN_TIMEOUT_SECONDS) but no overall pipeline timeout.
- **Duplicate upload:** Same checksum+course reuses document; policy (reuse vs version) not documented. Transaction: document + chunks written in one commit but no explicit rollback path if chunk write fails mid-way.
- **Security:** Filename sanitized with `secure_filename`; auth/role on routes; no CORS restriction by default (empty CORS_ALLOWED_ORIGINS); secrets in config, not in logs (provider logs request_id, not keys).

---

## 2. Architecture Decision

- **Canonical document API:** **`/api/cscl/courses/<course_id>/docs/*`** is the single document API. Use it for upload, list, delete, and any future prefill.
- **No `/api/teacher/documents/*`:** Do not reintroduce teacher-specific document routes; avoid duplicate maintenance.
- **Compatibility redirects:** Add only if a legacy client is identified; otherwise not required.

---

## 3. Gap Items (Blockers / Major / Minor)

### Blockers (must fix before server push)

| # | Symptom | Root cause hypothesis | Affected files | Fix plan | Risk |
|---|--------|----------------------|----------------|----------|------|
| B1 | RAG finds no documents when teacher runs pipeline after uploading to “course documents” | Frontend uses `course_id = 'default-course'` for docs; script is created with `course_id = course_context.subject`. Retriever filters by `script.course_id`. | `static/js/teacher.js` (loadDocuments, uploadDocument, create script payload) | Use a single course_id for teacher flow: e.g. derive from current script or use a fixed default (e.g. `default-course`) for both document upload/list and script creation so script.course_id matches docs. Document the contract. | High |
| B2 | Pipeline can run with invalid or missing course/doc context | No preflight check that required fields, course ownership, and doc/chunk availability are satisfied before starting pipeline. | `app/routes/cscl.py` (run_pipeline), `app/services/cscl_pipeline_service.py` | Add preflight step (or endpoint): required spec fields, course_id present, document/chunks available for that course, provider readiness. Return actionable JSON errors; do not start run if preflight fails. | Medium |
| B3 | API error shape inconsistent; HTML possible on unhandled errors | Some routes return `error`+`code`, others `valid`+`issues`; Flask may return HTML for 500/404 if not caught. | All API route handlers, error handlers | Standardize API error JSON: `{ success: false, error_code, message, details?, trace_id? }`. Ensure all API routes return JSON (register API error handler that returns JSON for 4xx/5xx). | Medium |

### Major (should fix)

| # | Symptom | Root cause hypothesis | Affected files | Fix plan | Risk |
|---|--------|----------------------|----------------|----------|------|
| M1 | Large or slow PDF blocks request | No timeout on upload or PDF extraction. | `app/services/document_service.py`, upload route | Add configurable upload/extraction timeout; consider background job for very large PDFs or enforce strict size + short timeout and return 413/504 with standard error body. | Medium |
| M2 | FILE_TOO_LARGE returns 400 with generic body | Upload handler maps specific error_codes to status but FILE_TOO_LARGE falls to generic 400. | `app/routes/cscl.py` (upload_course_document) | Map error_code FILE_TOO_LARGE to 413 and include standard error JSON. | Low |
| M3 | No prefill from document → high teacher effort | Form is filled only by demo or manual input; no extraction of course_title, learning_outcomes, task_type, etc. from uploaded doc. | New prefill service + route, frontend | Add POST /api/cscl/courses/<course_id>/docs/<doc_id>/prefill returning structured fields with confidence/source; UI to show prefilled form and “accept high-confidence” / require confirmation for low-confidence. | Medium |
| M4 | Duplicate upload policy unclear; storage not verified | Same file (checksum+course) reuses doc; no doc explaining reuse vs version. get_course_documents does not check storage_uri existence. | `app/services/document_service.py`, docs | Document “reuse by checksum” in runbook; optionally add storage_uri existence check in list and return warning in metadata. | Low |
| M5 | Double-click on “Run pipeline” creates two runs | No idempotency key for pipeline run creation. | `app/routes/cscl.py`, `app/services/cscl_pipeline_service.py`, frontend | Accept idempotency key (e.g. header or body); return existing run if key repeated within window. Frontend disable button after first click. | Low |
| M6 | Extraction metadata incomplete | Backend does not return page_count; extraction_method and warnings exist but page_count would help UX. | `app/services/document_service.py`, `app/routes/cscl.py` | In extract_text_from_pdf_bytes (or equivalent), add page_count; include in extraction_metadata and response. | Low |

### Minor (polish)

| # | Symptom | Root cause hypothesis | Affected files | Fix plan | Risk |
|---|--------|----------------------|----------------|----------|------|
| N1 | No /api/health/deps for ops | Only /api/health; no granular db/provider/storage check. | `app/routes/api.py` | Add GET /api/health/deps (or query param) returning db, provider, storage (e.g. upload dir writable) for diagnostics. | Low |
| N2 | No request_id in API error responses | Harder to correlate logs with client errors. | API error helper, routes | Add trace_id/request_id to standard error JSON; set request-scoped id in middleware or at route start. | Low |
| N3 | Frontend looks generic; weak hierarchy/colors | Current UI is functional but “AI-looking,” weak visual hierarchy. | `static/css/*.css`, `templates/teacher.html` | Design tokens (neutral + primary + accent), spacing/typography, card/button states, empty/loading/error states (Phase D). | Low |
| N4 | No fallback PDF extractor | Scanned/image PDFs yield no text; user gets generic parse failure. | `app/services/document_service.py` | Add optional fallback (e.g. OCR or alternate library) behind config; deterministic post-validation; document limitations. | Low |

---

## 4. Execution Plan (Ordered by Risk)

1. **B1 — course_id alignment**  
   Fix document vs script course_id so RAG can find uploaded docs. Unblock end-to-end teacher flow.  
   **Then:** B2 (pipeline preflight), B3 (error contract).

2. **B2 — Pipeline preflight**  
   Validate required fields, course, doc/chunks, provider before creating a run. Reduces wasted runs and unclear failures.

3. **B3 — Standard API error contract**  
   One JSON shape for all API errors; ensure no HTML body for API routes. Enables consistent client handling and FILE_TOO_LARGE → 413 (M2).

4. **M2 — FILE_TOO_LARGE → 413**  
   Quick follow-up to B3.

5. **M1 — Upload/extraction timeout**  
   Configurable timeout and size limit; return 413/504 with JSON.

6. **M5 — Pipeline idempotency**  
   Idempotency key + button disable to prevent duplicate runs.

7. **M4 — Duplicate/storage policy**  
   Document reuse; optional storage_uri check in list.

8. **M6 — page_count in extraction**  
   Add to PDF extraction and response.

9. **M3 — Prefill engine**  
   New prefill endpoint + UI (Phase C).

10. **N1, N2 — Observability**  
    /api/health/deps, request_id in errors.

11. **N3 — Frontend redesign**  
    Phase D design system and workflow screens.

12. **N4 — PDF fallback**  
    Optional fallback extractor with safe output.

---

## 5. What Remains Before All-Student Rollout

- **Reliability:** After B1–B3 and M1–M5: stable upload/list, preflight, error contract, timeouts, idempotency. Remaining risk: very large or corrupted PDFs; mitigate with limits and timeouts.
- **Teacher cognitive load:** M3 (prefill) and N3 (UX) reduce effort and confusion; not blocking for “works correctly” but needed for “polished and low-cognitive-load.”
- **Security:** Auth and role checks in place; CORS and secrets handling should be reviewed for production host (Phase B5). Risk: low if env is configured per runbook.
- **Observability:** N1/N2 and structured logs (upload → extraction → prefill → pipeline) improve ops; recommend before full rollout.
- **Risk grading:**  
  - **Blockers B1–B3:** Must be fixed before server push (high confidence).  
  - **Major M1–M6:** Should be fixed for production-ready quality (medium confidence).  
  - **Minor N1–N4:** Polish and ops; can follow in first iteration or shortly after (low risk to defer partially).

---

## 6. File Reference (Key Files)

| Area | Files |
|------|--------|
| Routes | `app/__init__.py`, `app/routes/cscl.py`, `app/routes/auth.py`, `app/routes/api.py`, `app/routes/teacher.py` |
| Upload / extraction | `app/services/document_service.py` |
| Pipeline | `app/services/cscl_pipeline_service.py`, `app/services/cscl_llm_provider.py` |
| Spec | `app/services/spec_validator.py`, `app/schemas/pedagogical_spec.py` |
| Frontend | `templates/teacher.html`, `static/js/teacher.js`, `static/css/teacher.css`, `static/css/style.css` |
| Config | `app/config.py` |
| Models | `app/models.py` (CSCLCourseDocument, CSCLDocumentChunk, CSCLScript, etc.) |

---

*End of Phase A. Next: Phase B (Backend hardening) per execution plan above.*
