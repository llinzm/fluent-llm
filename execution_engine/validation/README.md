# Validation Module

## Purpose

The validation module is the bridge between:
- the capability registry
- the workflow/planner layers
- the LLM feedback loop

It validates steps and workflows using stable, structured checks and turns
failures into machine-readable feedback and LLM-ready retry prompts.

## Components

### `validator_wrapper.py`
Wraps registry-level validation and adds workflow/planner-facing checks:
- required-field validation
- tip volume validation
- liquid-class / tip compatibility
- labware presence validation
- warnings for unspecified fields

### `feedback_builder.py`
Transforms validation results into:
- typed `ValidationFeedback`
- prompt-ready text for iterative regeneration

It also defines the **error taxonomy**, which standardizes issue types.

## Why this module matters

This module turns:
`validation failure`
into:
`actionable, structured guidance`

That is what enables the system to become self-correcting rather than a
one-shot planner.

## Typical flow

```python
result = validator.validate_step(step)

if not result.valid:
    prompt = feedback_builder.build_retry_prompt(result)
    # send prompt back to LLM for regeneration
```

## Design principles

- clean separation of concerns
- deterministic validation
- structured error taxonomy
- prompt-friendly feedback generation
- tolerant of evolving registry structure
