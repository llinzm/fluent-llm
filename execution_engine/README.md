# 🧠 Execution Engine — AI-Driven Lab Automation (Tecan Fluent)

## 🎯 Overview

The `execution_engine` is a modular Python package that transforms a **natural language lab protocol (IFU)** into a **validated, optimized, and executable workflow** on Tecan Fluent systems.

It acts as a **compiler + optimizer + runtime bridge** for laboratory automation.

---

## 🧱 Core Concept

```text
Natural Language (IFU)
        ↓
        LLM
        ↓
Structured Assay Model (TDF / JSON)
        ↓
Validation Engine
        ↓
Execution Planner
        ↓
PyFluent Runtime Adapter
        ↓
FluentControl Execution
```

---

## 🧠 What This System Does

The system:

* Converts human-readable protocols into structured workflows
* Validates against real hardware constraints (tips, volumes, labware)
* Optimizes execution using a capability-driven planner
* Executes workflows step-by-step via FluentControl
* Provides structured feedback to LLMs when errors occur

---

## 🧩 Package Structure

```text
execution_engine/
│
├── capability_registry/      # System capabilities (devices, tips, liquids, labware)
├── models/                   # Core data structures (Step, Workflow, Plan, Feedback)
├── workflow/                 # Assay decomposition + state tracking
├── planner/                  # Method selection + scoring engine
├── validation/               # Constraint validation + LLM feedback
├── runtime/                  # Execution adapters (PyFluent)
├── orchestration/            # End-to-end execution loop
│
└── README.md
```

---

## ⚙️ Key Components

### 1. Workflow Layer

Transforms high-level assay steps into atomic operations.

```python
workflow = decomposer.decompose(assay)
```

---

### 2. Validation Layer

Ensures physical and system constraints are respected.

* Tip capacity
* Liquid compatibility
* Labware constraints

```python
result = validator.validate_workflow(workflow)
```

If invalid:

```python
prompt = feedback_builder.build_retry_prompt(result)
```

---

### 3. Planner (Core Intelligence)

Selects the best execution method per step using:

* capability registry
* constraint-aware scoring
* efficiency heuristics

```python
plan = planner.plan(step)
```

---

### 4. Runtime Adapter

Executes selected methods via FluentControl:

```python
runtime.run_method(method_name, variables)
```

---

### 5. Orchestration Layer

Coordinates the full execution:

```python
result = execution_loop.run(assay)
```

Handles:

* decomposition
* validation
* feedback loop
* planning
* execution
* state updates

---

## 🔁 Feedback Loop (Critical)

If validation fails, the system generates structured feedback:

```json
{
  "type": "tip_volume_exceeded",
  "message": "Volume exceeds tip capacity",
  "suggestion": ["Use larger tip"]
}
```

This is converted into an LLM prompt:

```text
The assay you generated is invalid.
Please correct the following issues...
```

👉 This enables **iterative refinement** of the assay.

---

## 🧪 Minimal Example

```python
from execution_engine.orchestration import ExecutionLoop

# Assume these are already initialized
execution_loop = ExecutionLoop(
    decomposer=decomposer,
    validator=validator,
    feedback_builder=feedback_builder,
    planner=planner,
    runtime_adapter=runtime,
    state_manager=state_manager,
)

assay = {
    "steps": [
        {"type": "reagent_distribution", "params": {"volume_uL": 50}},
        {"type": "incubate", "params": {"time": 600}}
    ]
}

result = execution_loop.run(assay)

if not result.success:
    print(result.retry_prompt)
else:
    print("Execution completed")
```

---

## 🧠 Design Principles

### 1. Separation of Concerns

* Registry = knowledge
* Validation = safety
* Planner = intelligence
* Runtime = execution
* Orchestration = coordination

---

### 2. Deterministic Behavior

Same input → same execution plan

---

### 3. Registry-Driven Logic

All decisions are based on capability definitions

---

### 4. Explainability

Each plan includes reasoning and scoring breakdown

---

### 5. Self-Correcting System

Validation → Feedback → LLM → Improved Assay

---

## 🚀 What Makes This Different

This is not just automation.

It is:

```text
A compiler and optimizer for biological workflows
```

Where:

* Assay = program
* Registry = constraints
* Planner = optimizer
* Runtime = execution engine

---

## 🔮 Future Extensions

* Automatic tip selection
* Multi-instrument orchestration
* Parallel execution (DAG workflows)
* Learning-based optimization
* Real-time state reconciliation

---

## 📌 Summary

The `execution_engine` turns:

```text
Human intent → Validated → Optimized → Executable lab workflows
```

With safety, determinism, and scalability at its core.
