from dataclasses import dataclass, field
from typing import Dict, List, Optional

STEP_SCHEMA = {
    "reagent_distribution": {
        "required": ["labware_source", "labware_target", "volumes"],
        "optional": [
            "sample_count",
            "DiTi_type",
            "DiTi_waste",
            "selected_wells_source",
            "selected_wells_target",
            "liquid_class",
            "labware_empty_tips",
        ],
    },
    "sample_transfer": {
        "required": ["labware_source", "labware_target", "volumes"],
        "optional": [
            "sample_count",
            "DiTi_type",
            "DiTi_waste",
            "selected_wells_source",
            "selected_wells_target",
            "liquid_class",
            "tips_per_well_source",
            "sample_direction",
            "number_replicates",
            "replicate_direction",
            "labware_empty_tips",
        ],
    },
    "aspirate_volume": {
        "required": ["labware", "volumes"],
        "optional": ["liquid_class", "well_offset", "well_offsets"],
    },
    "dispense_volume": {
        "required": ["labware", "volumes"],
        "optional": ["liquid_class", "well_offset", "well_offsets"],
    },
    "mix_volume": {
        "required": ["labware", "volumes"],
        "optional": ["liquid_class", "well_offset", "well_offsets", "cycles"],
    },
    "incubate": {
        "required": ["labware", "location"],
        "optional": ["time_s"],
    },
    "transfer_labware": {
        "required": ["labware_name", "target_location"],
        "optional": ["target_position"],
    },
    "get_tips": {
        "required": ["diti_type"],
        "optional": [],
    },
    "drop_tips_to_location": {
        "required": ["labware"],
        "optional": [],
    },
    "empty_tips": {
        "required": ["labware"],
        "optional": ["well_offsets", "liquid_class"],
    },
    "reagent_distribution_simple": {
        "required": ["source", "target", "volume_uL"],
        "optional": ["liquid", "liquid_class", "tip_type"],
    },
    "mix": {
        "required": ["target", "volume_uL"],
        "optional": ["cycles", "liquid_class", "tip_type"],
    },
}

@dataclass
class Step:
    type: str
    params: Dict = field(default_factory=dict)
    id: Optional[str] = None

@dataclass
class Workflow:
    steps: List[Step]
