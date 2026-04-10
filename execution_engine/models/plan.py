from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Plan:
    method_name: str
    variables: Dict[str, Any]
    score: float
    reasoning: Dict[str, Any]
