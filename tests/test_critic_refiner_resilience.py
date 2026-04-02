"""Resilience tests for CriticRefiner stage."""
from app.services.pipeline.critic_refiner import CriticRefinerStage


class _ProviderSuccessSoftIssue:
    def critique_and_refine(self, input_payload):
        return {
            "success": True,
            "provider": "mock",
            "model": "mock-model",
            "result": {
                "validation": {
                    "is_valid": False,
                    "issues": ["Course grounding is limited in one step."],
                    "warnings": [],
                },
                "quality_indicators": {"scene_count": 1, "role_count": 1, "scriptlet_count": 1},
                "roles": [{"role_name": "facilitator", "responsibilities": ["guide discussion"]}],
                "scenes": [
                    {
                        "order_index": 1,
                        "scene_type": "opening",
                        "purpose": "start",
                        "transition_rule": "next",
                        "scriptlets": [{"prompt_text": "Do X", "prompt_type": "claim", "role_id": None}],
                    }
                ],
            },
        }


class _ProviderFailed:
    def critique_and_refine(self, input_payload):
        return {"success": False, "provider": "mock", "model": "mock-model", "error": "timeout"}


class _ProviderRaises:
    def critique_and_refine(self, input_payload):
        raise RuntimeError("network down")


def _material_output():
    return {
        "roles": [{"role_name": "analyst", "responsibilities": ["analyze evidence"]}],
        "scenes": [
            {
                "order_index": 1,
                "scene_type": "opening",
                "purpose": "kickoff",
                "transition_rule": "continue",
                "scriptlets": [{"prompt_text": "Read and discuss", "prompt_type": "claim", "role_id": None}],
            }
        ],
        "student_worksheet": {"title": "Worksheet A"},
    }


def test_soft_validation_issue_is_not_blocking_when_output_usable():
    stage = CriticRefinerStage(provider=_ProviderSuccessSoftIssue())
    result = stage.run(_material_output(), {"course_context": {"topic": "X"}}, {"run_id": "test-1"})
    assert result["status"] == "success"
    assert result["error"] is None
    assert result["output_snapshot"]["scenes"]


def test_provider_failure_falls_back_to_material_output():
    stage = CriticRefinerStage(provider=_ProviderFailed())
    result = stage.run(_material_output(), {"course_context": {"topic": "X"}}, {"run_id": "test-2"})
    assert result["status"] == "success"
    assert result["output_snapshot"]["scenes"]
    assert result["output_snapshot"]["student_worksheet"]["title"] == "Worksheet A"


def test_provider_exception_falls_back_to_material_output():
    stage = CriticRefinerStage(provider=_ProviderRaises())
    result = stage.run(_material_output(), {"course_context": {"topic": "X"}}, {"run_id": "test-3"})
    assert result["status"] == "success"
    assert result["output_snapshot"]["roles"][0]["role_name"] == "analyst"


def test_provider_failure_without_material_output_returns_failed():
    stage = CriticRefinerStage(provider=_ProviderFailed())
    result = stage.run({}, {"course_context": {"topic": "X"}}, {"run_id": "test-4"})
    assert result["status"] == "failed"
    assert result["output_snapshot"] is None
