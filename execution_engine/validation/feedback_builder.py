from typing import Dict, List

from execution_engine.models.feedback import FeedbackItem, ValidationFeedback


ERROR_TAXONOMY: Dict[str, Dict[str, str]] = {
    "missing_required_field": {
        "category": "schema",
        "llm_guidance": "Regenerate the assay with all required fields present for the affected step."
    },
    "unknown_tip_type": {
        "category": "registry",
        "llm_guidance": "Use a tip type that exists in the capability registry."
    },
    "tip_volume_exceeded": {
        "category": "volume",
        "llm_guidance": "Use a larger tip or split the transfer into smaller operations."
    },
    "tip_volume_below_minimum": {
        "category": "volume",
        "llm_guidance": "Use a smaller tip or adjust the transferred volume."
    },
    "unknown_liquid_class": {
        "category": "registry",
        "llm_guidance": "Use a liquid class defined in the capability registry."
    },
    "liquid_tip_incompatibility": {
        "category": "compatibility",
        "llm_guidance": "Choose a tip compatible with the liquid class, or change the liquid class."
    },
    "unknown_labware": {
        "category": "registry",
        "llm_guidance": "Use configured labware or extend the capability registry."
    },
    "tip_not_specified": {
        "category": "inference",
        "llm_guidance": "Specify the tip explicitly or rely on planner-side tip selection."
    },
    "liquid_class_not_specified": {
        "category": "inference",
        "llm_guidance": "Specify the liquid class explicitly or enable liquid inference."
    },
    "registry_validation_error": {
        "category": "registry",
        "llm_guidance": "Regenerate the assay so that it respects capability-registry constraints."
    },
}


class FeedbackBuilder:
    """
    Converts structured validation results into:
    1) typed feedback objects for application logic
    2) prompt-ready text for LLM retry / refinement
    """

    def build_feedback(self, validation_result) -> ValidationFeedback:
        return validation_result.to_feedback()

    def build_retry_prompt(self, validation_result, original_format: str = "JSON") -> str:
        feedback = self.build_feedback(validation_result)

        lines: List[str] = []
        lines.append("The assay you generated is invalid.")
        lines.append("")
        if feedback.errors:
            lines.append("Issues:")
            for idx, err in enumerate(feedback.errors, start=1):
                lines.extend(self._render_feedback_item(idx, err))
        if feedback.warnings:
            lines.append("")
            lines.append("Warnings:")
            for idx, warn in enumerate(feedback.warnings, start=1):
                lines.extend(self._render_feedback_item(idx, warn, numbered=False))

        lines.append("")
        lines.append("Please regenerate a corrected assay in the same {} format.".format(original_format))
        lines.append("Do not change steps that are already valid unless needed to fix the issues above.")
        lines.append("Respect the capability registry constraints.")

        return "\n".join(lines)

    def _render_feedback_item(self, idx: int, item: FeedbackItem, numbered: bool = True) -> List[str]:
        prefix = f"{idx}. " if numbered else "- "
        lines = [f"{prefix}{item.message}"]

        taxonomy = ERROR_TAXONOMY.get(item.type, {})
        guidance = taxonomy.get("llm_guidance")
        if guidance:
            lines.append(f"   Guidance: {guidance}")

        if item.suggestion:
            lines.append(f"   Suggestions: {', '.join(item.suggestion)}")

        if item.context:
            # Keep it compact and readable for prompt use
            compact = ", ".join([f"{k}={v}" for k, v in item.context.items()])
            lines.append(f"   Context: {compact}")

        return lines
