from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from execution_engine.models.feedback import FeedbackItem, ValidationFeedback
from execution_engine.models.workflow import Step, STEP_SCHEMA


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
    Validation layer around workflow steps and capability-registry constraints.

    Responsibilities:
    - schema validation using STEP_SCHEMA
    - semantic validation (volume / liquid / labware)
    - normalization across evolving field names
    - structured feedback generation
    """

    TRANSFER_STEP_TYPES = {
        "reagent_distribution",
        "sample_transfer",
        "aspirate_volume",
        "dispense_volume",
        "mix_volume",
        "reagent_distribution_simple",
        "mix",
    }

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

        errors.extend(self._validate_tip_volume(step))
        errors.extend(self._validate_liquid_tip_compatibility(step))
        errors.extend(self._validate_labware_presence(step))
        warnings.extend(self._validate_unknowns(step))

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_workflow(self, workflow) -> ValidationResult:
        all_errors: List[Dict[str, Any]] = []
        all_warnings: List[Dict[str, Any]] = []

        for idx, step in enumerate(workflow.steps):
            schema = STEP_SCHEMA.get(step.type)
            if schema is None:
                all_errors.append(
                    self._make_issue(
                        issue_type="unknown_step_type",
                        message=f"Unknown step type '{step.type}'",
                        severity="error",
                        suggestion=["Use a supported step type defined in STEP_SCHEMA."],
                        context={"step_type": step.type, "step_index": idx},
                    )
                )
            else:
                required_fields = schema.get("required", [])
                missing = [f for f in required_fields if step.params.get(f) in (None, "")]
                if missing:
                    all_errors.append(
                        self._make_issue(
                            issue_type="missing_required_field",
                            message=f"Missing required fields for step '{step.type}': {missing}",
                            severity="error",
                            suggestion=[f"Add values for: {', '.join(missing)}"],
                            context={
                                "step_type": step.type,
                                "missing_fields": missing,
                                "step_index": idx,
                            },
                        )
                    )

            result = self.validate_step(step)

            for err in result.errors:
                err.setdefault("context", {})
                err["context"]["step_index"] = idx

            for warn in result.warnings:
                warn.setdefault("context", {})
                warn["context"]["step_index"] = idx

            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        return ValidationResult(
            valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
        )

    def _validate_tip_volume(self, step: Step) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        volume = self._extract_volume(step)
        tip_type = self._extract_tip_type(step)

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
        liquid_class = self._extract_liquid_class(step)
        tip_type = self._extract_tip_type(step)

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
        roles: List[Tuple[str, Any]] = []

        for field_name in ["source", "target", "labware", "labware_source", "labware_target", "labware_empty_tips", "labware_name"]:
            value = step.params.get(field_name)
            if value not in (None, ""):
                roles.append((field_name, value))

        for role, value in roles:
            if not self._labware_exists(value):
                issues.append(
                    self._make_issue(
                        issue_type="unknown_labware",
                        message=f"{role} '{value}' is not present in the capability registry",
                        severity="error",
                        suggestion=["Use a configured labware entry", "Extend the registry with this labware"],
                        context={"role": role, "labware": value},
                    )
                )

        return issues

    def _validate_unknowns(self, step: Step) -> List[Dict[str, Any]]:
        warnings: List[Dict[str, Any]] = []

        if step.type in self.TRANSFER_STEP_TYPES:
            if self._extract_tip_type(step) is None:
                warnings.append(
                    self._make_issue(
                        issue_type="tip_not_specified",
                        message="No tip type specified; planner may need to infer or select a tip later",
                        severity="warning",
                        suggestion=["Provide a tip type or enable automatic tip selection"],
                        context={"step_type": step.type},
                    )
                )
            if self._extract_liquid_class(step) is None:
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

    def _extract_tip_type(self, step: Step) -> Optional[str]:
        return (
            step.params.get("tip_type")
            or step.params.get("DiTi_type")
            or step.params.get("diti_type")
        )

    def _extract_volume(self, step: Step) -> Optional[Any]:
        return step.params.get("volume_uL") if step.params.get("volume_uL") is not None else step.params.get("volumes")

    def _extract_liquid_class(self, step: Step) -> Optional[str]:
        return step.params.get("liquid_class")

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
