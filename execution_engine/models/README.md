# 🧱 Models — Core Data Contracts

## 🎯 Overview

The `models` package defines the **core data structures (contracts)** of the execution engine.

These models are the **shared language** between all components:

- LLM / Workflow generation
- Validation
- Planning
- Execution

👉 In short:  
**Everything flows through these models**

---

## 🧱 Data Flow Role

IFU / LLM
 ↓
Workflow / Step
 ↓
Validation
 ↓
Plan
 ↓
Execution (State updates)
 ↓
Feedback

---

## 🧩 Modules

### 1. workflow.py

Defines the **intermediate representation (IR)** of an assay.

```python
@dataclass
class Step:
    type: str
    params: Dict

@dataclass
class Workflow:
    steps: List[Step]
```

Also defines `STEP_SCHEMA`

👉 This is the **contract between LLM and system**

---

### 2. plan.py

Represents the output of the planner.

```python
@dataclass
class Plan:
    method_name: str
    variables: Dict[str, Any]
    score: float
    reasoning: Dict[str, Any]
```

👉 This is what gets executed downstream

---

### 3. state.py

Tracks runtime execution state.

```python
@dataclass
class State:
    well_volumes: Dict[str, float]
    tip_loaded: bool
```

👉 Enables simulation, validation, and future feedback loops

---

### 4. feedback.py

Defines structured validation feedback.

```python
@dataclass
class FeedbackItem:
    type: str
    message: str
    suggestion: List[str]
    context: Dict[str, Any]
    severity: str

@dataclass
class ValidationFeedback:
    errors: List[FeedbackItem]
    warnings: List[FeedbackItem]
```

👉 Used for LLM retry loops and debugging

---

## ⚙️ How Models Connect

### Workflow → Validation

```python
workflow = Workflow(steps=[Step(...)])
validator.validate_workflow(workflow)
```

---

### Step → Plan

```python
plan = planner.plan(step)
```

---

### Plan → Execution

```python
adapter.execute(plan)
```

---

### Validation → Feedback

```python
feedback = validation_result.to_feedback()
```

---

## 🧠 Key Concepts

### 1. Single Source of Truth

- All layers depend on these models
- Prevents mismatch between modules

---

### 2. Strong Contracts

- `Workflow` = input contract
- `Plan` = execution contract
- `ValidationFeedback` = correction contract

---

### 3. LLM Compatibility

Models are:
- JSON-serializable
- Simple
- Explicit

👉 Ideal for prompt-based generation

---

### 4. STEP_SCHEMA = Guardrail

```python
STEP_SCHEMA = {
    "reagent_distribution": ["source", "target", "volume_uL"],
    "mix": ["target", "volume_uL"],
    "incubate": ["labware", "location"],
}
```

👉 Defines **minimum valid structure**

---

## 🧪 Minimal Example

```python
from execution_engine.models.workflow import Workflow, Step

workflow = Workflow(
    steps=[
        Step(
            type="reagent_distribution",
            params={
                "volume_uL": 50,
                "source": "Trough_25mL:A1",
                "target": "Plate_96:A1"
            }
        )
    ]
)
```

---

## ⚠️ Design Rules

- Keep models **simple and explicit**
- Avoid logic inside models (pure data)
- Ensure backward compatibility
- Prefer adding fields over changing structure

---

## 🚀 Future Extensions

- Typed params per step type (strong typing)
- Versioned schemas
- Serialization helpers (JSON ↔ objects)
- State evolution tracking
- Plan execution logs

---

## 📌 Summary

Models are the **foundation of the system**:

```text
LLM → Workflow → Validation → Plan → Execution → Feedback
```

They ensure every layer speaks the same language.
