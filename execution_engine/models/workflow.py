
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Step:
    type: str
    params: Dict = field(default_factory=dict)
    id: Optional[str] = None

@dataclass
class Workflow:
    steps: List[Step]
