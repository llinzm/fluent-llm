
from dataclasses import dataclass, field
from typing import List, Dict, Optional

STEP_SCHEMA = {
    "reagent_distribution": ["source", "target", "volume_uL"],
    "mix": ["target", "volume_uL"],
    "incubate": ["labware", "location"],
}

@dataclass
class Step:
    type: str
    params: Dict = field(default_factory=dict)
    id: Optional[str] = None

@dataclass
class Workflow:
    steps: List[Step]
