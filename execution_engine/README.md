# 🧠 Execution Engine — AI-Driven Lab Automation (Tecan Fluent)

## 🎯 Overview

The `execution_engine` is a modular Python package that transforms a **natural language lab protocol (IFU)** into a **validated, optimized, and executable workflow** on Tecan Fluent systems.

It acts as a **compiler + optimizer + runtime bridge** for laboratory automation.

---

## 🧱 Core Concept (End-to-End)

```text
Natural Language (IFU)
        ↓
LLM Module (PromptBuilder + LLMClient)
        ↓
Structured Assay Model (TDF / JSON)
        ↓
Workflow Decomposition
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
* Enforces **structured JSON output from LLMs**
* Validates against real hardware constraints (tips, volumes, labware)
* Optimizes execution using a capability-driven planner
* Executes workflows step-by-step via FluentControl
* Provides structured feedback to LLMs when errors occur (self-correcting loop)

---

## 🧩 Package Structure

```text
execution_engine/
│
├── capability_registry/      # System capabilities (devices, tips, liquids, labware)
├── llm/                      # IFU → TDF (PromptBuilder + LLMClient)
├── models/                   # Core data structures (Step, Workflow, Plan, Feedback)
├── workflow/                 # Assay decomposition + state tracking
├── planner/                  # Method selection + scoring engine
├── validation/               # Constraint validation + LLM feedback
├── runtime/                  # Execution adapters (PyFluent)
├── orchestration/            # End-to-end execution loop
├── utils/                    # Logging, helpers
│
└── README.md
```

---

## ⚙️ Key Components

### 1. LLM Layer (Entry Point)

Transforms IFU → structured assay (TDF)

```python
from execution_engine.llm import LLMClient

client = LLMClient()
tdf = client.generate_tdf(ifu_text)
```

✔ Structured JSON enforced
✔ Retry loop on invalid output
✔ Capability hints supported

---

### 2. Workflow Layer

Transforms TDF into executable workflow steps.

```python
workflow = decomposer.decompose(tdf)
```

---

### 3. Validation Layer

Ensures physical and system constraints are respected.

* tip capacity
* liquid compatibility
* labware constraints

```python
result = validator.validate_workflow(workflow)
```

If invalid:

```python
retry_prompt = feedback_builder.build_retry_prompt(result)
```

👉 This feeds back into the LLM

---

### 4. Planner (Core Intelligence)

Selects the best execution method per step using:

* capability registry
* constraint-aware scoring
* efficiency heuristics

```python
plan = planner.plan(step)
```

---

### 5. Runtime Adapter (PyFluent)

Executes selected methods via FluentControl:

```python
runtime.run_method(method_name, variables)
```

Supports:

* MethodManager mode
* Low-level runtime mode

---

### 6. Orchestration Layer

Coordinates the full execution pipeline:

```python
result = execution_loop.run(ifu_text)
```

Handles:

* IFU → TDF (LLM)
* decomposition
* validation
* feedback loop
* planning
* execution
* state updates

---

## 🔁 Feedback Loop (Critical)

If validation fails, structured feedback is generated:

```json
{
  "type": "tip_volume_exceeded",
  "message": "Volume exceeds tip capacity",
  "suggestion": ["Use larger tip"]
}
```

Converted into LLM retry prompt:

```text
The assay you generated is invalid.
Fix the following issues...
```

👉 Enables **self-correcting workflows**

---

## 🧪 Minimal End-to-End Example

```python
from execution_engine.llm import LLMClient
from execution_engine.orchestration import ExecutionLoop

# Initialize components (simplified)
llm = LLMClient()
execution_loop = ExecutionLoop(...)

ifu = """
Distribute 50 µL buffer into a 96-well plate.
Incubate for 10 minutes.
"""

# Step 1: IFU → TDF
tdf = llm.generate_tdf(ifu)

# Step 2: Execute
result = execution_loop.run(tdf)

if not result.success:
    print(result.retry_prompt)
else:
    print("Execution completed")
```

---

## 🧠 Design Principles

### 1. Separation of Concerns

* Registry → knowledge
* LLM → interpretation
* Validation → safety
* Planner → intelligence
* Runtime → execution
* Orchestration → coordination

---

### 2. Deterministic Execution

Same TDF → same execution plan

---

### 3. Registry-Driven Logic

All decisions rely on explicit capability definitions

---

### 4. Explainability

Each plan includes:

* score
* reasoning
* constraint evaluation

---

### 5. Self-Correcting System

```text
LLM → Validation → Feedback → LLM → Improved TDF
```

---

## 🚀 What Makes This Different

This is not just automation.

It is:

```text
A compiler and optimizer for biological workflows
```

Where:

* IFU = source code
* TDF = intermediate representation
* Registry = hardware constraints
* Planner = optimizer
* Runtime = execution engine

---

## 🔮 Future Extensions

* Automatic tip & liquid class inference
* Multi-instrument orchestration
* Parallel workflow execution (DAG)
* Learning-based optimization
* Real-time telemetry feedback loop

---

## 📌 Summary

The `execution_engine` turns:

```text
Human intent → Structured → Validated → Optimized → Executed
```

With safety, explainability, and scalability at its core.
