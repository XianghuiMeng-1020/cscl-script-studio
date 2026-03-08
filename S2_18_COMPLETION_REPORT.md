# S2.18 Completion Report: Provider Fallback + Fail-Fast

## Goal
Unblock pipeline by implementing provider fallback and explicit fail-fast guard. Proposal-first, no demo shortcut, production-safe.

## Changes Implemented

### 1. Provider Routing (Backend) - Never Pick Unimplemented OpenAI

**File**: `app/services/cscl_llm_provider.py`

- Added `_is_provider_runnable(name)` function:
  - Mock: always runnable
  - OpenAI: runnable only if `OPENAI_ENABLED=true` AND `OPENAI_IMPLEMENTED=true` AND has API key
  - Qwen: runnable if has API key (implementation assumed complete)

- Modified `get_cscl_llm_provider(force_provider=None)`:
  - Deterministic selection: if primary not runnable, use fallback automatically
  - Never selects unimplemented OpenAI as active provider
  - Supports `force_provider` parameter for retry scenarios

- Added `get_llm_provider_status()` function:
  - Returns `{llm_provider_ready, llm_provider_name, llm_provider_reason}`
  - Used by health endpoint and pipeline fail-fast check

- Enhanced `FallbackLLMProvider`:
  - Records `stage_attempts` for pipeline logging
  - Includes "not fully implemented" in retryable error patterns

### 2. Fail-Fast Guard in Pipeline/Run

**File**: `app/services/cscl_pipeline_service.py`

- Added provider readiness check before starting pipeline:
  - Calls `get_llm_provider_status()` at start
  - If not ready, returns immediately with `status='provider_not_ready'`
  - Does NOT create pipeline run record (fail-fast)

- Added fallback retry logic in planner stage:
  - If planner fails with "not fully implemented" error
  - Auto-switches to fallback provider and retries once
  - Records both attempts in `stage_attempts`
  - Updates pipeline provider chain if fallback succeeds

- Modified `__init__` to accept `force_provider` parameter

**File**: `app/routes/cscl.py`

- Updated `run_pipeline` route:
  - Extracts `force_provider` from `generation_options`
  - Returns 503 with `code=LLM_PROVIDER_NOT_READY` when provider not ready
  - Passes `force_provider` to `CSCLPipelineService`

### 3. Health Endpoint Updates

**File**: `app/routes/api.py`

- Updated `/api/health` endpoint:
  - Includes `llm_provider_ready` (bool)
  - Includes `llm_provider_name` (str)
  - Includes `llm_provider_reason` (str)
  - UI can check readiness before attempting pipeline run

### 4. Frontend Error UX

**File**: `static/js/teacher.js`

- Enhanced `showPipelineErrorPanel()`:
  - Accepts `showRetryButton` parameter
  - Displays retry button when appropriate

- Updated `runPipeline()`:
  - Handles 503 `LLM_PROVIDER_NOT_READY`: shows error panel with retry button
  - Handles 422 `PIPELINE_FAILED`: shows error panel with retry button
  - Preserves spec in `sessionStorage` for retry
  - Stops spinner and re-enables Run button on error
  - No infinite Pending state

- Added `retryPipelineWithFallback()`:
  - Restores spec from `sessionStorage`
  - Calls pipeline/run with `generation_options.force_provider='qwen'`
  - Handles errors gracefully

### 5. Config Cleanup

**File**: `app/config.py`

- Added configuration variables:
  - `LLM_PROVIDER_STRATEGY` (default: 'primary_with_fallback')
  - `LLM_PRIMARY` (default: 'openai')
  - `LLM_FALLBACK` (default: 'qwen')
  - `LLM_ALLOW_UNIMPLEMENTED_PRIMARY` (default: False)
  - `OPENAI_ENABLED` (default: False)
  - `OPENAI_IMPLEMENTED` (default: False)

**File**: `.env.example`

- Updated LLM Provider Configuration section:
  - Clarified: OpenAI enabled only when implemented
  - Default production-safe provider is qwen
  - Added explicit env vars with documentation

### 6. Tests

**File**: `tests/test_s2_18_provider_fallback.py`

- `test_health_exposes_llm_provider_ready_fields`: Verifies health endpoint includes required fields
- `test_pipeline_returns_503_when_no_runnable_provider`: Verifies fail-fast returns 503
- `test_pipeline_openai_unimplemented_auto_fallback_to_qwen`: Verifies fallback logic
- `test_get_llm_provider_status_mock`: Verifies status for mock provider
- `test_get_llm_provider_status_openai_not_implemented`: Verifies status when OpenAI not implemented

## Acceptance Criteria Verification

### ✅ Provider Fallback Success Path
```bash
curl -X POST http://localhost:5001/api/cscl/scripts/{script_id}/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"spec": {...}}'
```
- Returns 200 with stages completed, provider=qwen (or fallback)
- OR returns 503 LLM_PROVIDER_NOT_READY (never misleading pending)

### ✅ Provider-Not-Ready Fail-Fast Path
```bash
# When no provider is runnable:
curl -X POST http://localhost:5001/api/cscl/scripts/{script_id}/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"spec": {...}}'
```
- Returns 503 with:
  ```json
  {
    "code": "LLM_PROVIDER_NOT_READY",
    "error": "Configured LLM provider is not runnable",
    "details": {
      "selected": "...",
      "fallback": "...",
      "reason": "..."
    }
  }
  ```
- No pipeline run record created (fail-fast)
- No Pending stage cards

### ✅ No Raw PDF Binary in Response
- Verified: No PDF binary data in any response (existing guardrails remain)

### ✅ UI Step 3 Never Stuck in Pending
- Error handling stops spinner
- Re-enables Run button
- Shows actionable error message
- Provides retry button for recoverable errors

## Files Changed

1. `app/services/cscl_llm_provider.py` - Provider routing and health status
2. `app/services/cscl_pipeline_service.py` - Fail-fast and fallback retry
3. `app/routes/cscl.py` - 503 handling and force_provider support
4. `app/routes/api.py` - Health endpoint updates
5. `app/config.py` - New configuration variables
6. `static/js/teacher.js` - Frontend error UX and retry
7. `.env.example` - Config documentation
8. `tests/test_s2_18_provider_fallback.py` - New tests
9. `scripts/s2_18_verify.sh` - Verification script

## Testing

### Manual Testing
```bash
# 1. Health check
curl -s http://localhost:5001/api/health | jq .

# 2. Provider fallback (with valid spec)
curl -X POST http://localhost:5001/api/cscl/scripts/{script_id}/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"spec": {...}}'

# 3. Provider-not-ready (when no provider configured)
# Should return 503 LLM_PROVIDER_NOT_READY
```

### Automated Testing
```bash
# Run S2.18 tests
pytest tests/test_s2_18_provider_fallback.py -v

# Run verification script
./scripts/s2_18_verify.sh
```

## Production Safety

- ✅ Never selects unimplemented OpenAI
- ✅ Defaults to production-safe provider (qwen)
- ✅ Fail-fast prevents misleading Pending states
- ✅ Clear error messages with actionable guidance
- ✅ Retry mechanism for recoverable errors
- ✅ No raw binary data in responses

## Next Steps

1. Deploy to staging environment
2. Verify health endpoint in monitoring
3. Test provider fallback with real API keys
4. Monitor pipeline success rates
5. Update documentation with provider selection guide
