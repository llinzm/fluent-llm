
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from .models import Device, Labware, LiquidClass, MetaFlags, Method, Operation, RecordType, Rule, TipType
from .registry import CapabilityRegistry


class RegistryLoadError(ValueError):
    """Raised when the registry file is malformed or incomplete."""


def _ensure_mapping(data: Any, section: str) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise RegistryLoadError(f"Section '{section}' must be a mapping.")
    return data


def _build_devices(raw: Dict[str, Any]) -> Dict[str, Device]:
    items: Dict[str, Device] = {}
    for name, payload in raw.items():
        payload = dict(payload or {})
        items[name] = Device(
            name=name,
            type=str(payload.get("type", "unknown")),
            capabilities=list(payload.get("capabilities", [])),
            channels=list(payload.get("channels", [])),
            liquid_handling_mode=payload.get("liquid_handling_mode"),
            tip_modes=list(payload.get("tip_modes", [])),
            constraints=dict(payload.get("constraints", {})),
            meta=MetaFlags.from_mapping(payload.get("meta")),
        )
    return items


def _build_tips(raw: Dict[str, Any]) -> Dict[str, TipType]:
    items: Dict[str, TipType] = {}
    for name, payload in raw.items():
        payload = dict(payload or {})
        items[name] = TipType(
            name=name,
            type=str(payload.get("type", "unknown")),
            max_volume_uL=payload.get("max_volume_uL"),
            min_volume_uL=payload.get("min_volume_uL"),
            channels=list(payload.get("channels", [])),
            conductive=payload.get("conductive"),
            filter_options=list(payload.get("filter_options", [])),
            purity_levels=list(payload.get("purity_levels", [])),
            dynamic_threshold_uL=payload.get("dynamic_threshold_uL"),
            washable=payload.get("washable"),
            volume_range_uL=list(payload.get("volume_range_uL", [])),
            volume_ranges=dict(payload.get("volume_ranges", {})),
            meta=MetaFlags.from_mapping(payload.get("meta")),
        )
    return items


def _build_liquid_classes(raw: Dict[str, Any]) -> Dict[str, LiquidClass]:
    examples = _ensure_mapping(raw.get("examples", {}), "liquid_classes.examples")
    items: Dict[str, LiquidClass] = {}
    for name, payload in examples.items():
        payload = dict(payload or {})
        items[name] = LiquidClass(
            name=name,
            dispense_modes=list(payload.get("dispense_modes", [])),
            compatible_tip_types=list(payload.get("compatible_tip_types", [])),
            constraints=dict(payload.get("constraints", {})),
            meta=MetaFlags.from_mapping(payload.get("meta")),
        )
    return items


def _build_labware(raw: Dict[str, Any]) -> Dict[str, Labware]:
    types = _ensure_mapping(raw.get("types", {}), "labware.types")
    items: Dict[str, Labware] = {}
    for name, payload in types.items():
        payload = dict(payload or {})
        items[name] = Labware(
            name=name,
            type=str(payload.get("type", "plate")),
            format=payload.get("format"),
            geometry=list(payload.get("geometry", [])),
            max_volume_uL=payload.get("max_volume_uL"),
            channels=None if payload.get("channels") is None else str(payload.get("channels")),
            meta=MetaFlags.from_mapping(payload.get("meta")),
        )
    return items


def _build_records(raw: Dict[str, Any]) -> Dict[str, RecordType]:
    items: Dict[str, RecordType] = {}
    for code, payload in raw.items():
        payload = dict(payload or {})
        items[code] = RecordType(
            code=code,
            name=str(payload.get("name", code)),
            volume_range=payload.get("volume_range"),
            meta=MetaFlags.from_mapping(payload.get("meta")),
        )
    return items


def _build_operations(raw: Dict[str, Any]) -> Dict[str, Operation]:
    items: Dict[str, Operation] = {}
    for level in ("high_level", "low_level"):
        for name in raw.get(level, []):
            items[name] = Operation(name=name, level=level, meta=MetaFlags())
    return items


def _build_methods(raw: list[dict[str, Any]]) -> Dict[str, Method]:
    items: Dict[str, Method] = {}
    for payload in raw:
        payload = dict(payload or {})
        name = str(payload["name"])
        items[name] = Method(
            name=name,
            supports=list(payload.get("supports", [])),
            requires=list(payload.get("requires", [])),
            meta=MetaFlags.from_mapping(payload.get("meta")),
        )
    return items


def _build_rules(raw: list[dict[str, Any]]) -> Dict[str, Rule]:
    items: Dict[str, Rule] = {}
    for payload in raw:
        payload = dict(payload or {})
        name = str(payload["name"])
        items[name] = Rule(
            name=name,
            severity=str(payload.get("severity", "error")),
            logic=dict(payload.get("logic", {})),
            description=payload.get("description"),
            meta=MetaFlags.from_mapping(payload.get("meta")),
        )
    return items


def _validate_top_level(data: Dict[str, Any]) -> None:
    required = [
        "version",
        "devices",
        "tips",
        "liquid_classes",
        "labware",
        "records",
        "operations",
        "methods",
        "rules",
        "compatibility",
        "constraints",
    ]
    missing = [name for name in required if name not in data]
    if missing:
        raise RegistryLoadError(f"Missing required top-level sections: {', '.join(missing)}")


def load_registry(path: str | Path) -> CapabilityRegistry:
    registry_path = Path(path)
    with registry_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise RegistryLoadError("Registry file must decode to a mapping.")

    _validate_top_level(data)

    return CapabilityRegistry(
        version=str(data["version"]),
        meta=dict(data.get("meta", {})),
        devices=_build_devices(_ensure_mapping(data["devices"], "devices")),
        tips=_build_tips(_ensure_mapping(data["tips"], "tips")),
        liquid_classes=_build_liquid_classes(_ensure_mapping(data["liquid_classes"], "liquid_classes")),
        labware=_build_labware(_ensure_mapping(data["labware"], "labware")),
        records=_build_records(_ensure_mapping(data["records"], "records")),
        operations=_build_operations(_ensure_mapping(data["operations"], "operations")),
        methods=_build_methods(list(data.get("methods", []))),
        rules=_build_rules(list(data.get("rules", []))),
        compatibility=dict(data.get("compatibility", {})),
        consumable_properties=dict(data.get("consumable_properties", {})),
        constraints=dict(data.get("constraints", {})),
        gaps=list(data.get("gaps", [])),
    )


def load_default_registry() -> CapabilityRegistry:
    return load_registry(Path(__file__).resolve().parent / "data" / "registry.yaml")
