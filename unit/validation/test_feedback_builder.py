from execution_engine.validation.validator_wrapper import ValidationResult
from execution_engine.validation.feedback_builder import FeedbackBuilder, ERROR_TAXONOMY


def test_error_taxonomy_contains_core_entries():
    assert "tip_volume_exceeded" in ERROR_TAXONOMY
    assert "liquid_tip_incompatibility" in ERROR_TAXONOMY
    assert "missing_required_field" in ERROR_TAXONOMY
    assert "unknown_step_type" in ERROR_TAXONOMY


def test_build_retry_prompt_contains_human_readable_guidance():
    builder = FeedbackBuilder()

    result = ValidationResult(
        valid=False,
        errors=[
            {
                "type": "tip_volume_exceeded",
                "message": "Requested volume 300 µL exceeds tip capacity",
                "suggestion": ["Use a larger tip"],
                "context": {"requested_volume_uL": 300, "max_volume_uL": 200},
                "severity": "error",
            }
        ],
        warnings=[],
    )

    prompt = builder.build_retry_prompt(result)

    assert "The assay you generated is invalid." in prompt
    assert "Use a larger tip" in prompt
    assert "Please regenerate a corrected assay" in prompt


def test_build_feedback_returns_typed_objects():
    builder = FeedbackBuilder()

    result = ValidationResult(
        valid=False,
        errors=[
            {
                "type": "unknown_tip_type",
                "message": "Unknown tip type",
                "suggestion": ["Use a configured tip"],
                "context": {"tip_type": "BAD_TIP"},
                "severity": "error",
            }
        ],
        warnings=[],
    )

    feedback = builder.build_feedback(result)
    assert len(feedback.errors) == 1
    assert feedback.errors[0].type == "unknown_tip_type"
