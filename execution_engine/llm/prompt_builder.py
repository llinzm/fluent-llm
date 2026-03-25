from typing import Any, Dict, Optional


class PromptBuilder:
    """Builds prompts to convert IFU → Structured Assay Model (TDF / JSON)."""

    SYSTEM_PROMPT = """You are an expert in laboratory automation and assay planning.

Convert the user's IFU into a structured JSON workflow (TDF).

Rules:
- Output valid JSON only.
- Decompose compound assay actions into explicit workflow steps when appropriate.
- Preserve execution order.
- Include step parameters under 'params'.
- Do not invent missing physical facts silently.
- If something is missing or ambiguous, put it into 'open_questions' or 'assumptions'.
- Prefer concise but complete step definitions.
"""

    def build(
        self,
        ifu_text: str,
        capability_hints: Optional[Dict[str, Any]] = None,
        additional_context: Optional[str] = None,
    ) -> str:
        hints_block = ""
        if capability_hints:
            hints_block = f"\nCapability hints:\n{capability_hints}\n"

        context_block = ""
        if additional_context:
            context_block = f"\nAdditional context:\n{additional_context}\n"

        return f"""{self.SYSTEM_PROMPT}
{hints_block}{context_block}
IFU:
{ifu_text}

Return JSON matching the requested schema only.
"""
