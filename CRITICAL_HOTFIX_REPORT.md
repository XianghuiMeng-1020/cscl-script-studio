# Critical Hotfix Report — Proposal-First, No Demo Shortcuts

**Project:** GenAI-Supported Multimodal CSCL Script Generation for Collaborative Argumentation in Higher Education  
**Hotfix scope:** PDF binary leak (A), pipeline 422 handling (B), script/session consistency (C), proposal-aligned task types (D).

---

## 1) Changed files

| File | Change |
|------|--------|
| `app/services/document_service.py` | Single detector `is_probably_pdf_binary_text`; added `safe_preview_or_none()`; all preview paths use it; 422 message standardized; logging only length/hash_prefix (no raw text). |
| `app/routes/cscl.py` | PDF 422: `error`, `code`, `message`; upload response uses `safe_preview_or_none` for preview; pipeline 422 returns `SPEC_INVALID` with `issues: [{field, reason}]`. |
| `config/task_types.json` | Replaced with v1 proposal-aligned types: `structured_debate`, `evidence_comparison`, `perspective_synthesis`, `claim_counterclaim_roleplay`; each with `display_name`, `description`, `pedagogical_goal`, `expected_outputs`, `minimum_role_pattern`, `compatible_modalities`. |
| `app/services/task_type_config.py` | Default IDs updated to the four new types; fallback structure includes `display_name`, `pedagogical_goal`, `compatible_modalities`. |
| `templates/teacher.html` | Step 3: added `#pipelineErrorPanel` (title, list, action); task type select single option "Loading..." (filled by JS). |
| `static/js/teacher.js` | `loadTaskTypes()` fetches `/api/cscl/task-types`, fills select with `display_name`, `title`=description; `runPipeline()`: preflight validate, GET script before run (404→clear id + goToStep(2), 401→session expired), 422→show panel + goToStep(2) + highlight first field, `resetPipelineStageCards()` on error, `finally` always clears loading and run button; sessionStorage persist/restore `cscl_current_script_id`; all task_type defaults `structured_debate`. |
| `tests/test_cscl_spec_validation.py` | All `task_type` values updated to new ids; `test_task_types_api` expects the four new ids. |
| `tests/test_cscl_spec_validation_enhanced.py` | All `task_type`: `debate` → `structured_debate`. |
| `tests/test_cscl_pipeline_api.py` | Valid spec in pipeline run includes `description` and `requirements_text`; `task_type` → `structured_debate`; added `test_pipeline_run_422_returns_spec_invalid_with_issues`. |
| `tests/test_s2_15_pdf_no_binary_leak.py` | `test_api_upload_pdf_binary_returns_422`: assert status 422, `code`/`error` PDF_PARSE_FAILED, `message` present, body never contains `%PDF` or `stream`. |

---

## 2) Root cause and fix per blocker

**A) PDF binary leakage**  
- **Cause:** Extracted text (or chunk concatenation) could contain PDF markers and was returned in `extracted_text_preview` or built from chunks in the route.  
- **Fix:** One shared `safe_preview_or_none(text)` in `document_service`: returns `None` if `is_probably_pdf_binary_text(text)`, else truncated safe text. All upload paths (cached, new PDF, new text) and the route set preview only via this; if `None`, respond 422 with `error`, `code`, `message` and no preview. Logging only length/hash_prefix/error_class. Frontend already treats `code === 'PDF_PARSE_FAILED'` with toast and does not render server preview when binary is detected.

**B) Pipeline 422 hidden as endless pending**  
- **Cause:** 422 from pipeline/run did not return a machine-readable issue list; frontend did not show errors in Step 3 or navigate to Step 2.  
- **Fix:** Pipeline 422 returns `error: 'SPEC_INVALID'`, `code: 'SPEC_INVALID'`, `issues: [{field, reason}, ...]`, `message: 'Spec validation failed.'` (from `field_paths` + issues). Frontend: preflight validate; if 422, block run and show errors (and go to Step 2). On pipeline run 422, show `#pipelineErrorPanel` with issue list, goToStep(2), highlight first field, call `resetPipelineStageCards()`. In `finally`, always `showLoading(false)` and restore run button so stages never stay in endless “Pending”.

**C) Script/session consistency**  
- **Cause:** Stale `currentScriptId` after refresh or re-login led to “Script not found” or auth mismatch without clear recovery.  
- **Fix:** After creating a script, persist `currentScriptId` in `sessionStorage['cscl_current_script_id']`; on load, restore from sessionStorage. Before POST pipeline/run, GET `/api/cscl/scripts/{id}`: 404 → clear `currentScriptId` and sessionStorage, show “Script expired, please complete Step 2 again”, goToStep(2); 401 → show “Session expired, please login again”. All API calls use `credentials: 'include'`.

**D) Task types not proposal-aligned**  
- **Cause:** Arbitrary four types and labels not tied to collaborative argumentation theory.  
- **Fix:** Config and backend use only: `structured_debate`, `evidence_comparison`, `perspective_synthesis`, `claim_counterclaim_roleplay`. Each has `display_name`, `description`, `pedagogical_goal`, `expected_outputs`, `minimum_role_pattern`, `compatible_modalities`. Backend reads from `config/task_types.json` (and fallback in `task_type_config`). Frontend loads `/api/cscl/task-types` and builds the dropdown from it (no hardcoded list); tooltip = description.

---

## 3) Test names and intent

| Test | Intent |
|------|--------|
| `test_api_upload_pdf_binary_returns_422` (test_s2_15) | Binary PDF upload → 422, code PDF_PARSE_FAILED, body never contains `%PDF` or `stream`. |
| `test_pipeline_run_422_returns_spec_invalid_with_issues` (test_cscl_pipeline_api) | Invalid spec (e.g. missing `course_context.description`) → 422, code SPEC_INVALID, `issues` array with `field` and `reason`. |
| `test_task_types_api` (test_cscl_spec_validation) | GET task-types returns the four ids: structured_debate, evidence_comparison, perspective_synthesis, claim_counterclaim_roleplay. |
| Existing spec/pipeline tests | Updated to use new task_type ids and full spec (description, requirements_text) so validate and pipeline run remain 200 where applicable. |

---

## 4) Curl examples (real IDs from your env)

Replace `SCRIPT_ID` with an id returned from `POST /api/cscl/scripts` after login.

```bash
# Health
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/api/health

# Login (get session cookie)
curl -c cookies.txt -X POST -H "Content-Type: application/json" -d '{"user_id":"T001","password":"teacher123"}' http://127.0.0.1:5000/api/auth/login

# Validate spec (no upload)
curl -b cookies.txt -X POST -H "Content-Type: application/json" -d '{
  "course_context":{"subject":"S","topic":"T","class_size":20,"mode":"sync","duration":60,"description":"Context here"},
  "learning_objectives":{"knowledge":["K"],"skills":["S"]},
  "task_requirements":{"task_type":"structured_debate","expected_output":"O","collaboration_form":"group","requirements_text":"Req"}
}' http://127.0.0.1:5000/api/cscl/spec/validate

# Create script (get script id from response)
curl -b cookies.txt -X POST -H "Content-Type: application/json" -d '{"title":"Test","topic":"T","task_type":"structured_debate","duration_minutes":60}' http://127.0.0.1:5000/api/cscl/scripts

# Get script (404 if wrong id or different user)
curl -b cookies.txt -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/api/cscl/scripts/SCRIPT_ID

# Pipeline run with invalid spec (422 + issues)
curl -b cookies.txt -X POST -H "Content-Type: application/json" -d '{
  "spec":{
    "course_context":{"subject":"S","topic":"T","class_size":10,"mode":"sync","duration":60},
    "learning_objectives":{"knowledge":["K"],"skills":["S"]},
    "task_requirements":{"task_type":"structured_debate","expected_output":"O","collaboration_form":"group","requirements_text":"R"}
  }
}' http://127.0.0.1:5000/api/cscl/scripts/SCRIPT_ID/pipeline/run
# Expect 422, body with code SPEC_INVALID and issues[].field e.g. course_context.description

# PDF upload binary (422 PDF_PARSE_FAILED)
curl -b cookies.txt -X POST -F "file=@bad.pdf;type=application/pdf" -F "title=bad" http://127.0.0.1:5000/api/cscl/courses/default-course/docs/upload
# With bad.pdf containing %PDF- / stream: expect 422, code PDF_PARSE_FAILED, no %PDF in body
```

---

## 5) Step 3 error panel (screenshot description)

When pipeline/run returns 422 with `issues`, the UI shows:

- **Step 3** visible with the pipeline visualization.
- **Error panel** (`#pipelineErrorPanel`) no longer hidden: title “Spec validation failed.” (or `result.message`), list of items like `course_context.description (required)`, `task_requirements.requirements_text (required)`, and the line “Fix the fields in Step 2 and run again.”
- User is **navigated to Step 2** and the **first invalid field** (e.g. Course Context or Task Requirements) is **highlighted** (`.validation-error`) and **scrolled into view**.
- **Run** button and **stage cards** are reset (no endless “Pending” or “Running”); loading overlay is closed.

---

## 6) Acceptance gates

1. **Manual input (no Fill Demo, no upload)** can pass validate and proceed — unchanged; spec sent in canonical shape with all required fields.
2. **Binary PDF** never appears in UI; upload returns 422 with `PDF_PARSE_FAILED` and no `%PDF` in body; frontend toasts and does not render preview.
3. **Pipeline run failures** show exact issues in Step 3 panel and route user to fix fields (Step 2 + highlight).
4. **No endless pending** after failed run: `finally` clears loading and run button; `resetPipelineStageCards()` used on error.
5. **Script/session errors** are actionable: 404 → “Script expired, please complete Step 2 again” + goToStep(2); 401 → “Session expired, please login again.”
6. **New/updated tests** (PDF 422, pipeline 422, task types, spec/pipeline with new task_type and full spec) pass when run in your environment.

Run tests (from repo root, with venv activated):

```bash
pytest tests/test_s2_15_pdf_no_binary_leak.py tests/test_cscl_spec_validation.py tests/test_cscl_pipeline_api.py::test_pipeline_run_422_returns_spec_invalid_with_issues tests/test_cscl_spec_validation_enhanced.py -v
```

Fill in actual pytest pass/fail and any curl outputs with real `SCRIPT_ID` when you run them locally.
