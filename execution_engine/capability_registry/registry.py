
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from .models import Device, Labware, LiquidClass, Method, Operation, RecordType, Rule, TipType
from .validator import RegistryValidator


@dataclass
class CapabilityRegistry:
    version: str
    meta: Dict[str, Any]
    devices: Dict[str, Device]
    tips: Dict[str, TipType]
    liquid_classes: Dict[str, LiquidClass]
    labware: Dict[str, Labware]
    records: Dict[str, RecordType]
    operations: Dict[str, Operation]
    methods: Dict[str, Method]
    rules: Dict[str, Rule]
    compatibility: Dict[str, Any]
    consumable_properties: Dict[str, Any]
    constraints: Dict[str, Any]
    gaps: list[str]

    def get_device(self, name: str) -> Optional[Device]:
        return self.devices.get(name)

    def get_tip(self, name: str) -> Optional[TipType]:
        return self.tips.get(name)

    def get_liquid_class(self, name: str) -> Optional[LiquidClass]:
        return self.liquid_classes.get(name)

    def get_labware(self, name: str) -> Optional[Labware]:
        return self.labware.get(name)

    def get_method(self, name: str) -> Optional[Method]:
        return self.methods.get(name)

    def list_operations(self, level: Optional[str] = None) -> list[str]:
        if level is None:
            return sorted(self.operations.keys())
        return sorted([name for name, op in self.operations.items() if op.level == level])

    def methods_supporting(self, operation_names: Iterable[str]) -> list[Method]:
        required = set(operation_names)
        return [
            method
            for method in self.methods.values()
            if required.issubset(set(method.supports))
        ]

    def is_tip_compatible_with_device(self, tip_name: str, device_name: str) -> bool:
        allowed = self.compatibility.get("tip_to_device", {}).get(device_name, [])
        return tip_name in allowed

    def recommended_labware_for_operation(self, operation_name: str) -> Dict[str, list[str]]:
        return self.compatibility.get("labware_to_operation", {}).get(operation_name, {})

    def validate_compatibility(
        self,
        *,
        device_name: Optional[str] = None,
        tip_name: Optional[str] = None,
        liquid_class_name: Optional[str] = None,
        volume_uL: Optional[float] = None,
        labware_name: Optional[str] = None,
        operation_name: Optional[str] = None,
    ):
        validator = RegistryValidator(self)
        return validator.validate(
            device_name=device_name,
            tip_name=tip_name,
            liquid_class_name=liquid_class_name,
            volume_uL=volume_uL,
            labware_name=labware_name,
            operation_name=operation_name,
        )
