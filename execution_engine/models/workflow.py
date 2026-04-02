
from dataclasses import dataclass, field
from typing import List, Dict, Optional

STEP_SCHEMA = {
    #"reagent_distribution": ["source", "target", "volume_uL"],
    "mix": ["target", "volume_uL"],
    "incubate": ["labware", "location"],
    "get_tips": ["diti_type","airgap_volume", "airgap_speed", "tip_indices"],
    "drop_tips_to_location": ["labware", "well_offsets", "tip_indices", "airgap_volume", "airgap_speed"],
    "aspirate_volume": ["volumes", "labware", "liquid_class", "well_offsets", "tip_indices"],
    "dispense_volume": ["volumes", "labware", "liquid_class", "well_offsets", "tip_indices"],
    "mix_volume": ["volumes", "labware", "liquid_class", "well_offsets", "tip_indices", "cycles"],
    "empty_tips": ["labware", "liquid_class", "well_offsets", "tip_indices"],
    "reagent_distribution": [
        "labware_empty_tips", 
        "volumes","sample_count",
        "DiTi_type","DiTi_waste",
        "labware_source",
        "labware_target",
        "selected_wells_source",
        "selected_wells_target",
        "liquid_class",
        "DynamicDiTiHandling",
        "DynamicDiTiHandling_rule",
        "LiquidClass_EmptyTip",
        "max_tip_reuse",
        "multi_dispense",
        "sample_direction", 
        "number_replicates", 
        "replicate_direction", 
        "airgap_volume", 
        "airgap_speed", 
        "tips_per_well_source", 
        "well_offset_source", 
        "tips_per_well_target", 
        "well_offset_target", 
        "tip_indices"
    ],
    "sample_transfer": [
        "labware_empty_tips",
        "volumes",
        "sample_count",
        "DiTi_type",
        "DiTi_waste",
        "labware_source",
        "labware_target",
        "selected_wells_source",
        "selected_wells_target",
        "liquid_class",
        "DynamicDiTiHandling",
        "DynamicDiTiHandling_rule",
        "pooling",
        "samples_per_pool",
        "LiquidClass_EmptyTip",
        "max_tip_reuse",
        "multi_dispense",
        "sample_direction",
        "number_replicates",
        "replicate_direction",
        "airgap_volume",
        "airgap_speed",
        "tips_per_well_source",
        "well_offset_source",
        "tips_per_well_target",
        "well_offset_target",
        "tip_indices",
    ],
    "transfer_labware": ["labware_name", "target_location", "target_position", "only_use_selected_site"],
}

@dataclass
class Step:
    type: str
    params: Dict = field(default_factory=dict)
    id: Optional[str] = None

@dataclass
class Workflow:
    steps: List[Step]
