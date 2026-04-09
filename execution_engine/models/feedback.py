from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class FeedbackItem:
    type: str
    message: str
    suggestion: List[str]
    context: Dict[str, Any]
    severity: str

@dataclass
class ValidationFeedback:
    errors: List[FeedbackItem]
    warnings: List[FeedbackItem]
