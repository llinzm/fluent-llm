# 🧪 Validation — Safety & Feedback Engine

## 🎯 Overview

The `validation` package is the safety and correctness layer of the execution engine.

It ensures that workflows are:
- structurally valid against `STEP_SCHEMA`
- semantically valid (tips, volumes, liquids, labware)
- aligned with system capabilities through the registry

It also converts failures into structured feedback for retry loops.

👉 In short: **Workflow → Valid / Invalid → Actionable Feedback**

---

## 🧩 Modules

### 1. `validator_wrapper.py`
Main validation entry point.

Responsibilities:
- workflow-level schema validation
- step-level semantic validation
- registry integration
- structured error / warning generation

### 2. `feedback_builder.py`
Converts validation results into:
- typed feedback objects
- LLM-ready retry prompts

### 3. Error taxonomy
Standardizes issue types such as:
- `missing_required_field`
- `unknown_step_type`
- `tip_volume_exceeded`
- `unknown_labware`
- `liquid_tip_incompatibility`

---

## 🧱 Validation Flow

```text
Workflow
↓
STEP_SCHEMA validation
↓
Step semantic validation
↓
Registry-aware checks
↓
Structured errors / warnings
↓
FeedbackBuilder → retry prompt
```

---

## ⚙️ What gets validated

### Schema validation
Uses `STEP_SCHEMA` from `execution_engine.models.workflow`.

Example:
```python
required_fields = STEP_SCHEMA[step.type]["required"]
```

This checks that each step includes the minimum required parameters.

### Semantic validation
Checks values such as:
- tip volume within allowed range
- liquid class compatibility with tip type
- existence of referenced labware

### Registry validation
If a lower-level registry validator is provided, it is called and any exceptions are normalized into structured issues.

---

## 🧪 Minimal Example

```python
from execution_engine.models.workflow import Workflow, Step
from execution_engine.validation.validator_wrapper import ValidatorWrapper
from execution_engine.validation.feedback_builder import FeedbackBuilder

workflow = Workflow(
    steps=[
        Step(
            type="sample_transfer",
            params={
                "labware_source": "sample_plate",
                "labware_target": "dilution_plate",
                "volumes": 25,
                "DiTi_type": "FCA_DiTi_200uL",
                "liquid_class": "Water_Free",
            },
        )
    ]
)

validator = ValidatorWrapper(registry)
result = validator.validate_workflow(workflow)

if not result.valid:
    feedback_builder = FeedbackBuilder()
    prompt = feedback_builder.build_retry_prompt(result)
    print(prompt)
```

---

## 🔁 Retry Loop Usage

Typical orchestration pattern:

```python
result = validator.validate_workflow(workflow)

if not result.valid:
    retry_prompt = feedback_builder.build_retry_prompt(result)
    # send retry_prompt back to LLM
```

Library / deterministic mode can fail fast without retry.

---

## 🧠 Design Principles

- `STEP_SCHEMA` is the single source of truth for required fields
- semantic validation stays separate from structural validation
- validation returns structured data, not ad hoc strings
- field aliases are supported where needed (`tip_type`, `DiTi_type`, `diti_type`)

---

## 📌 Summary

The validation package is both:

```text
Safety gate
```

and

```text
Bridge to intelligent correction
```

It protects execution while enabling retry-driven improvement of workflows.
