from dataclasses import dataclass, field
from typing import Dict

@dataclass
class State:
    well_volumes: Dict[str, float] = field(default_factory=dict)
    tip_loaded: bool = False
