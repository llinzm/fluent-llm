# 🧱 Models — Core Data Contracts

## 🎯 Overview

The `models` package defines the shared data structures of the execution engine.

These models are the contract between:
- LLM / TDF generation
- workflow decomposition
- validation
- planning
- runtime execution
- feedback loops

👉 In short: **all modules speak through these models**

---

## 🧩 Modules

### 1. `workflow.py`
Defines the workflow intermediate representation (IR):

- `Step`
- `Workflow`
- `STEP_SCHEMA`

`STEP_SCHEMA` is the structural contract for each step type.

It separates:
- `required` parameters
- `optional` parameters

Example:

```python
from execution_engine.models.workflow import Step, Workflow

workflow = Workflow(
    steps=[
        Step(
            type="sample_transfer",
            params={
                "labware_source": "sample_plate",
                "labware_target": "dilution_plate",
                "volumes": 25,
            }
        )
    ]
)
```

### 2. `plan.py`
Defines the output of the planner:

- `Plan`

### 3. `state.py`
Defines lightweight execution state:

- `State`

### 4. `feedback.py`
Defines structured validation feedback:

- `FeedbackItem`
- `ValidationFeedback`

---

## 🧠 Why this package matters

The models package gives the system:
- stable contracts between modules
- a clear workflow IR
- schema-driven validation
- structured planner output
- structured feedback for retries

---

## 📌 Summary

The models package is the **contract layer** of the execution engine:

```text
LLM / Library → Workflow → Validation → Plan → Execution → Feedback
```
