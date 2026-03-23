
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class MetaFlags:
    documented: bool = False
    inferred: bool = False
    unknown: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: Optional[Dict[str, Any]]) -> "MetaFlags":
        value = value or {}
        return cls(
            documented=bool(value.get("documented", False)),
            inferred=bool(value.get("inferred", False)),
            unknown=bool(value.get("unknown", False)),
            extra={k: v for k, v in value.items() if k not in {"documented", "inferred", "unknown"}},
        )


@dataclass(frozen=True)
class Device:
    name: str
    type: str
    capabilities: List[str] = field(default_factory=list)
    channels: List[Any] = field(default_factory=list)
    liquid_handling_mode: Optional[str] = None
    tip_modes: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    meta: MetaFlags = field(default_factory=MetaFlags)


@dataclass(frozen=True)
class TipType:
    name: str
    type: str
    max_volume_uL: Optional[float] = None
    min_volume_uL: Optional[float] = None
    channels: List[Any] = field(default_factory=list)
    conductive: Optional[bool] = None
    filter_options: List[str] = field(default_factory=list)
    purity_levels: List[str] = field(default_factory=list)
    dynamic_threshold_uL: Optional[float] = None
    washable: Optional[bool] = None
    volume_range_uL: List[Any] = field(default_factory=list)
    volume_ranges: Dict[str, Any] = field(default_factory=dict)
    meta: MetaFlags = field(default_factory=MetaFlags)


@dataclass(frozen=True)
class LiquidClass:
    name: str
    dispense_modes: List[str] = field(default_factory=list)
    compatible_tip_types: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    meta: MetaFlags = field(default_factory=MetaFlags)


@dataclass(frozen=True)
class Labware:
    name: str
    type: str
    format: Optional[str] = None
    geometry: List[Any] = field(default_factory=list)
    max_volume_uL: Optional[float] = None
    channels: Optional[str] = None
    meta: MetaFlags = field(default_factory=MetaFlags)


@dataclass(frozen=True)
class RecordType:
    code: str
    name: str
    volume_range: Optional[str] = None
    meta: MetaFlags = field(default_factory=MetaFlags)


@dataclass(frozen=True)
class Operation:
    name: str
    level: str
    meta: MetaFlags = field(default_factory=MetaFlags)


@dataclass(frozen=True)
class Method:
    name: str
    supports: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)
    meta: MetaFlags = field(default_factory=MetaFlags)


@dataclass(frozen=True)
class Rule:
    name: str
    severity: str = "error"
    logic: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    meta: MetaFlags = field(default_factory=MetaFlags)


@dataclass(frozen=True)
class ValidationIssue:
    rule: str
    severity: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, issue: ValidationIssue) -> None:
        if issue.severity.lower() == "warning":
            self.warnings.append(issue)
        else:
            self.errors.append(issue)
