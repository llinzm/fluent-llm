
from __future__ import annotations

from typing import Optional

from .models import ValidationIssue, ValidationResult


class RegistryValidator:
    """Validation engine for compatibility checks driven by the registry."""

    def __init__(self, registry):
        self.registry = registry

    def validate(
        self,
        *,
        device_name: Optional[str] = None,
        tip_name: Optional[str] = None,
        liquid_class_name: Optional[str] = None,
        volume_uL: Optional[float] = None,
        labware_name: Optional[str] = None,
        operation_name: Optional[str] = None,
    ) -> ValidationResult:
        result = ValidationResult()

        device = self.registry.get_device(device_name) if device_name else None
        tip = self.registry.get_tip(tip_name) if tip_name else None
        liquid_class = self.registry.get_liquid_class(liquid_class_name) if liquid_class_name else None
        labware = self.registry.get_labware(labware_name) if labware_name else None

        if device_name and device is None:
            result.add(ValidationIssue("device_exists", "error", f"Unknown device: {device_name}"))
        if tip_name and tip is None:
            result.add(ValidationIssue("tip_exists", "error", f"Unknown tip: {tip_name}"))
        if liquid_class_name and liquid_class is None:
            result.add(ValidationIssue("liquid_class_exists", "error", f"Unknown liquid class: {liquid_class_name}"))
        if labware_name and labware is None:
            result.add(ValidationIssue("labware_exists", "error", f"Unknown labware: {labware_name}"))

        if device and tip_name and not self.registry.is_tip_compatible_with_device(tip_name, device.name):
            result.add(
                ValidationIssue(
                    "tip_to_device_compatibility",
                    "error",
                    f"Tip '{tip_name}' is not compatible with device '{device.name}'.",
                    context={"device": device.name, "tip": tip_name},
                )
            )

        if tip and volume_uL is not None and tip.max_volume_uL is not None and volume_uL > tip.max_volume_uL:
            result.add(
                ValidationIssue(
                    "tip_volume_limit",
                    "error",
                    f"Requested volume {volume_uL} µL exceeds tip limit of {tip.max_volume_uL} µL.",
                    context={"tip": tip.name, "volume_uL": volume_uL},
                )
            )

        if tip and volume_uL is not None and tip.min_volume_uL is not None and volume_uL < tip.min_volume_uL:
            result.add(
                ValidationIssue(
                    "tip_min_volume_limit",
                    "warning",
                    f"Requested volume {volume_uL} µL is below the configured minimum of {tip.min_volume_uL} µL.",
                    context={"tip": tip.name, "volume_uL": volume_uL},
                )
            )

        if liquid_class and tip_name and liquid_class.compatible_tip_types:
            if tip_name not in liquid_class.compatible_tip_types:
                result.add(
                    ValidationIssue(
                        "liquid_class_tip_compatibility",
                        "error",
                        f"Liquid class '{liquid_class.name}' is not marked as compatible with tip '{tip_name}'.",
                        context={"liquid_class": liquid_class.name, "tip": tip_name},
                    )
                )

        if operation_name and device:
            operation = self.registry.operations.get(operation_name)
            if operation is None:
                result.add(
                    ValidationIssue("operation_exists", "error", f"Unknown operation: {operation_name}")
                )
            elif operation_name not in device.capabilities and operation.level == "low_level":
                result.add(
                    ValidationIssue(
                        "device_capability_required",
                        "error",
                        f"Device '{device.name}' does not advertise low-level capability '{operation_name}'.",
                        context={"device": device.name, "operation": operation_name},
                    )
                )

        if operation_name and labware:
            compat = self.registry.compatibility.get("labware_to_operation", {}).get(operation_name, {})
            allowed = set(compat.get("compatible", [])) | set(compat.get("recommended", []))
            if allowed and labware.name not in allowed:
                result.add(
                    ValidationIssue(
                        "labware_to_operation_compatibility",
                        "warning",
                        f"Labware '{labware.name}' is not listed as compatible/recommended for '{operation_name}'.",
                        context={"labware": labware.name, "operation": operation_name},
                    )
                )

        if device and tip:
            if tip.type == "fixed" and device.name == "FCA":
                result.add(
                    ValidationIssue(
                        "fixed_tip_on_fca",
                        "error",
                        "FCA is configured only for disposable tips in this registry.",
                        context={"device": device.name, "tip": tip.name},
                    )
                )

        return result
