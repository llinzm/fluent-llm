
from execution_engine.models.feedback import FeedbackItem, ValidationFeedback

def test_feedback():
    item = FeedbackItem(
        type="error",
        message="msg",
        suggestion=["fix"],
        context={},
        severity="error"
    )
    fb = ValidationFeedback(errors=[item], warnings=[])
    assert len(fb.errors) == 1
