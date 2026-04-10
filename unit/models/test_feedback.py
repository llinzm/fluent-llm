from execution_engine.models.feedback import FeedbackItem, ValidationFeedback

def test_feedback_structure():
    item = FeedbackItem(
        type="missing_required_field",
        message="Missing required fields",
        suggestion=["Add values for: target"],
        context={"step_type": "mix"},
        severity="error",
    )
    feedback = ValidationFeedback(errors=[item], warnings=[])
    assert len(feedback.errors) == 1
    assert feedback.errors[0].severity == "error"
