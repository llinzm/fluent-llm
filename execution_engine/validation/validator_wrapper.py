from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from execution_engine.models.feedback import FeedbackItem, ValidationFeedback
from execution_engine.models.workflow import Step


@dataclass
class ValidationResult:
    valid: bool
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    def to_feedback(self) -> ValidationFeedback:
        return ValidationFeedback(
            errors=[FeedbackItem(**e) for e in self.errors],
            warnings=[FeedbackItem(**w) for w in self.warnings],
        )


class ValidatorWrapper:
    """
    Thin orchestration layer around capability-registry validation.

    Responsibilities:
    - normalize validation around workflow Step objects
    - apply additional planner/runtime-facing checks
    - return structured errors/warnings for the feedback loop

    Notes:
    - This wrapper is intentionally tolerant of evolving registry shapes
      (dict-like or object-like).
    - It can work even if a lower-level registry validator is not yet
      fully implemented, by applying wrapper-level checks.
    """

    def __init__(self, registry, registry_validator: Optional[Any] = None):
        self.registry = registry
        self.registry_validator = registry_validator

    def validate_step(self, step: Step) -> ValidationResult:
        errors: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []

        if self.registry_validator is not None:
            try:
                try:
                    self.registry_validator.validate_step(step, self.registry)
                except TypeError:
                    self.registry_validator.validate_step(step)
            except Exception as exc:
                errors.append(
                    self._make_issue(
                        issue_type="registry_validation_error",
                        message=str(exc),
                        severity="error",
                        suggestion=["Review registry-level constraints for this step."],
                        context={"step_type": step.type, "step_params": step.params},
                    )
                )

        errors.extend(self._validate_required_fields(step))
        errors.extend(self._validate_tip_volume(step))
        errors.extend(self._validate_liquid_tip_compatibility(step))
        errors.extend(self._validate_labware_presence(step))
        warnings.extend(self._validate_unknowns(step))

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_workflow(self, workflow) -> ValidationResult:
        all_errors: List[Dict[str, Any]] = []
        all_warnings: List[Dict[str, Any]] = []

        for idx, step in enumerate(workflow.steps):
            result = self.validate_step(step)
            for err in result.errors:
                err.setdefault("context", {})
                err["context"]["step_index"] = idx
            for warn in result.warnings:
                warn.setdefault("context", {})
                warn["context"]["step_index"] = idx
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        return ValidationResult(valid=len(all_errors) == 0, errors=all_errors, warnings=all_warnings)

    def _validate_required_fields(self, step: Step) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        required_by_step = {
            "reagent_distribution": ["volume_uL", "source", "target"],
            "aspirate": ["volume_uL", "source"],
            "dispense": ["volume_uL", "target"],
            "mix": ["target"],
            "incubate": [],
        }

        required = required_by_step.get(step.type, [])
        missing = [field for field in required if step.params.get(field) in (None, "")]
        if missing:
            issues.append(
                self._make_issue(
                    issue_type="missing_required_field",
                    message=f"Missing required fields for step '{step.type}': {missing}",
                    severity="error",
                    suggestion=[f"Add values for: {', '.join(missing)}"],
                    context={"step_type": step.type, "missing_fields": missing},
                )
            )
        return issues

    def _validate_tip_volume(self, step: Step) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        volume = step.params.get("volume_uL")
        tip_type = step.params.get("tip_type")

        if volume is None or tip_type is None:
            return issues

        tip = self._get_tip(tip_type)
        if not tip:
            issues.append(
                self._make_issue(
                    issue_type="unknown_tip_type",
                    message=f"Unknown tip type: {tip_type}",
                    severity="error",
                    suggestion=["Use a configured tip from the capability registry."],
                    context={"tip_type": tip_type},
                )
            )
            return issues

        max_vol = self._value(tip, "max_volume_uL")
        if max_vol is None:
            max_vol = self._value(tip, "max_volume")
        min_vol = self._value(tip, "min_volume_uL")

        if max_vol is not None and volume > max_vol:
            issues.append(
                self._make_issue(
                    issue_type="tip_volume_exceeded",
                    message=f"Requested volume {volume} µL exceeds tip capacity ({max_vol} µL) for {tip_type}",
                    severity="error",
                    suggestion=["Use a larger tip", "Split the transfer into multiple dispenses"],
                    context={"tip_type": tip_type, "requested_volume_uL": volume, "max_volume_uL": max_vol},
                )
            )
        if min_vol is not None and volume < min_vol:
            issues.append(
                self._make_issue(
                    issue_type="tip_volume_below_minimum",
                    message=f"Requested volume {volume} µL is below minimum supported volume ({min_vol} µL) for {tip_type}",
                    severity="warning",
                    suggestion=["Use a smaller tip or adjust the assay volume"],
                    context={"tip_type": tip_type, "requested_volume_uL": volume, "min_volume_uL": min_vol},
                )
            )
        return issues

    def _validate_liquid_tip_compatibility(self, step: Step) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        liquid_class = step.params.get("liquid_class")
        tip_type = step.params.get("tip_type")

        if not liquid_class or not tip_type:
            return issues

        lc = self._get_liquid_class(liquid_class)
        if not lc:
            issues.append(
                self._make_issue(
                    issue_type="unknown_liquid_class",
                    message=f"Unknown liquid class: {liquid_class}",
                    severity="error",
                    suggestion=["Use a configured liquid class from the capability registry."],
                    context={"liquid_class": liquid_class},
                )
            )
            return issues

        compatible = self._value(lc, "compatible_tip_types")
        if not compatible:
            compatible = self._value(lc, "compatible_tips")
        compatible = compatible or []

        if compatible and tip_type not in compatible:
            issues.append(
                self._make_issue(
                    issue_type="liquid_tip_incompatibility",
                    message=f"Liquid class '{liquid_class}' is incompatible with tip '{tip_type}'",
                    severity="error",
                    suggestion=["Choose a compatible tip", "Use a compatible liquid class"],
                    context={"liquid_class": liquid_class, "tip_type": tip_type, "compatible_tips": compatible},
                )
            )
        return issues

    def _validate_labware_presence(self, step: Step) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        for role in ("source", "target"):
            value = step.params.get(role)
            if not value:
                continue

            if not self._labware_exists(value):
                severity = "error" if step.type in ("reagent_distribution", "aspirate", "dispense", "mix") else "warning"
                issues.append(
                    self._make_issue(
                        issue_type="unknown_labware",
                        message=f"{role.title()} labware '{value}' is not present in the capability registry",
                        severity=severity,
                        suggestion=["Use a configured labware entry", "Extend the registry with this labware"],
                        context={"role": role, "labware": value},
                    )
                )
        return issues

    def _validate_unknowns(self, step: Step) -> List[Dict[str, Any]]:
        warnings: List[Dict[str, Any]] = []
        if not step.params.get("tip_type"):
            warnings.append(
                self._make_issue(
                    issue_type="tip_not_specified",
                    message="No tip type specified; planner may need to infer or select a tip later",
                    severity="warning",
                    suggestion=["Provide a tip type or enable automatic tip selection"],
                    context={"step_type": step.type},
                )
            )
        if not step.params.get("liquid_class"):
            warnings.append(
                self._make_issue(
                    issue_type="liquid_class_not_specified",
                    message="No liquid class specified; planner may need to infer it later",
                    severity="warning",
                    suggestion=["Provide a liquid class or enable liquid class inference"],
                    context={"step_type": step.type},
                )
            )
        return warnings

    def _get_tip(self, tip_type: str) -> Optional[Any]:
        if hasattr(self.registry, "get_tip"):
            return self.registry.get_tip(tip_type)
        tips = getattr(self.registry, "tips", {})
        return tips.get(tip_type) if isinstance(tips, dict) else None

    def _get_liquid_class(self, liquid_class: str) -> Optional[Any]:
        if hasattr(self.registry, "get_liquid_class"):
            return self.registry.get_liquid_class(liquid_class)
        lcs = getattr(self.registry, "liquid_classes", {})
        return lcs.get(liquid_class) if isinstance(lcs, dict) else None

    def _labware_exists(self, labware_name: str) -> bool:
        base_name = labware_name.split(":", 1)[0] if isinstance(labware_name, str) else labware_name
        labware = getattr(self.registry, "labware", None)

        if labware is not None and not isinstance(labware, dict):
            if hasattr(labware, "types"):
                types = getattr(labware, "types")
                if isinstance(types, dict) and base_name in types:
                    return True

        if isinstance(labware, dict):
            if base_name in labware:
                return True
            types = labware.get("types")
            if isinstance(types, dict) and base_name in types:
                return True
        return False

    @staticmethod
    def _value(obj: Any, key: str, default: Any = None) -> Any:
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    @staticmethod
    def _make_issue(issue_type: str, message: str, severity: str, suggestion: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": issue_type,
            "message": message,
            "suggestion": suggestion,
            "context": context,
            "severity": severity,
        }
