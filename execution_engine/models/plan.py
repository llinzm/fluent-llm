
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Plan:
    method_name: str
    variables: Dict[str, Any]
    score: float
    reasoning: Dict[str, Any]
