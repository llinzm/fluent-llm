
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class FeedbackItem:
    type: str
    message: str
    suggestion: List[str]
    context: Dict[str, Any]
    severity: str  # error or warning

@dataclass
class ValidationFeedback:
    errors: List[FeedbackItem]
    warnings: List[FeedbackItem]
