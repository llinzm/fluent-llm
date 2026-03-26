# 🧪 Validation — Safety & Feedback Engine

## 🎯 Overview

The `validation` package is the **safety and correctness layer** of the execution engine.

It ensures that workflows are:
- structurally valid (schema)
- physically feasible (tips, volumes, labware)
- compliant with system capabilities (registry)

It also transforms validation failures into **structured feedback** for retry loops.

👉 In short:  
**Workflow → Valid / Invalid → Actionable Feedback**

---

## 🧱 Validation Flow

Workflow
 ↓
Schema Validation (STEP_SCHEMA)
 ↓
Step Validation
 ↓
Registry Validation
 ↓
Errors / Warnings
 ↓
Feedback Builder
 ↓
Retry Prompt (LLM mode)

---

## 🧩 Modules

### 1. validator_wrapper.py (Core Validator)

Main entry point.

Responsibilities:
- Workflow-level validation
- Step-level validation
- Registry integration
- Structured error generation

```python
result = validator.validate_workflow(workflow)
```

---

### 2. feedback_builder.py

Transforms validation results into:

- Typed feedback objects
- LLM-ready retry prompts

```python
prompt = feedback_builder.build_retry_prompt(result)
```

---

### 3. Error Taxonomy

Defined in `feedback_builder.py`

Standardizes errors such as:
- missing_required_field
- tip_volume_exceeded
- unknown_labware
- liquid_tip_incompatibility

👉 Ensures consistent feedback across system

---

## ⚙️ How Validation Works

### Step 1 — Schema Validation

```python
required_fields = STEP_SCHEMA.get(step.type, [])
missing = [f for f in required_fields if step.params.get(f) in (None, "")]
```

Ensures structural correctness.

---

### Step 2 — Step Validation

```python
result = validator.validate_step(step)
```

Checks:
- tip volume limits
- liquid compatibility
- labware presence

---

### Step 3 — Registry Validation

```python
registry_validator.validate_step(step)
```

Ensures step aligns with system capabilities.

---

### Step 4 — Aggregate Results

```python
ValidationResult(
    valid=True/False,
    errors=[...],
    warnings=[...]
)
```

---

### Step 5 — Feedback Generation

```python
retry_prompt = feedback_builder.build_retry_prompt(result)
```

Produces:

```text
The assay you generated is invalid.
Fix the following issues...
```

---

## 🧪 Minimal Example

```python
from execution_engine.validation.validator_wrapper import ValidatorWrapper
from execution_engine.validation.feedback_builder import FeedbackBuilder

validator = ValidatorWrapper(registry)
feedback_builder = FeedbackBuilder()

result = validator.validate_workflow(workflow)

if not result.valid:
    prompt = feedback_builder.build_retry_prompt(result)
    print(prompt)
```

---

## 🧠 Key Concepts

### 1. Two-Level Validation

| Level | Purpose |
|------|--------|
| Workflow | schema validation |
| Step | semantic validation |

---

### 2. Separation of Concerns

- Schema → models (STEP_SCHEMA)
- Validation → this module
- Registry → capability_registry

---

### 3. Structured Feedback

All issues follow a consistent format:

```python
{
    "type": "...",
    "message": "...",
    "suggestion": [...],
    "context": {...},
    "severity": "error" | "warning"
}
```

---

### 4. Deterministic Behavior

Same input → same validation result

---

### 5. LLM Feedback Loop

```text
Validation → Feedback → LLM → Improved Workflow
```

---

## 🚀 Future Improvements

- Auto-repair suggestions (not just errors)
- Validation-aware planning
- Confidence scoring
- Runtime feedback integration

---

## 📌 Summary

The validation layer acts as the **safety gate**:

```text
Workflow → Checked → Safe → Executable
```

and as the **bridge to intelligence**:

```text
Failure → Structured Feedback → Self-Correction
```
