# 🧠 Execution Engine — AI-Driven Lab Automation (Tecan Fluent)

## 🎯 Overview

The `execution_engine` is a modular Python framework that transforms a **natural language lab protocol (IFU)** into a **validated, optimized, and executable workflow** on Tecan Fluent systems.

It acts as an **AI-powered compiler + optimizer + runtime bridge** for laboratory automation.

---

## 🧱 Core Concept (End-to-End)

```text
Natural Language (IFU) / TDF Library
        ↓
LLM Module (optional)
        ↓
Structured Assay Model (TDF / Workflow)
        ↓
Workflow Decomposition
        ↓
Validation (Schema + Registry + Constraints)
        ↓
Execution Planner (Method selection + scoring)
        ↓
Runtime Adapter (PyFluent)
        ↓
FluentControl Execution
        ↓
State Update
```

---

## 🧠 What This System Does

The system:

- Converts human-readable protocols into structured workflows
- Supports **LLM-generated or library-based workflows (TDF)**
- Enforces **schema + registry-driven validation**
- Optimizes execution using a capability-aware planner
- Executes workflows via FluentControl
- Provides structured feedback for retry loops (LLM mode)

---

## 🧩 Package Structure

```text
execution_engine/
│
├── capability_registry/   # Devices, methods, tips, labware, liquids
├── llm/                   # IFU → TDF (optional)
├── models/                # Core structures (Workflow, Step, Plan)
├── workflow/              # Decomposition + state handling
├── planner/               # Candidate selection + scoring
├── validation/            # Schema + constraint validation
├── runtime/               # PyFluent adapter
├── orchestration/         # Execution loop (core pipeline)
├── utils/                 # Helpers / logging
```

---

## 🧠 High-Level Architecture

```mermaid
flowchart LR

A[IFU or TDF Library] --> B[LLM (optional)]
B --> C[Workflow Decomposer]
C --> D[Workflow Object]

D --> E[Validation Layer]
E -->|Valid| F[Planner]
E -->|Invalid| G[Feedback Builder]
G --> B

F --> H[Execution Plan]
H --> I[Runtime Adapter]
I --> J[FluentControl]
J --> K[State Manager]
```

---

## ⚙️ Key Components

### 1. LLM Layer (Optional)

Transforms IFU → TDF

```python
tdf = llm.generate_tdf(ifu_text)
```

Supports:
- Structured JSON enforcement
- Retry on invalid outputs

---

### 2. Workflow Layer

```python
workflow = decomposer.decompose(tdf)
```

Transforms TDF → internal execution structure

---

### 3. Validation Layer

Ensures correctness:

- Required fields (STEP_SCHEMA)
- Tip / volume compatibility
- Labware presence
- Registry constraints

```python
result = validator.validate_workflow(workflow)
```

---

### 4. Planner (Core Intelligence)

Selects best execution method:

- Capability matching
- Constraint-aware scoring
- Variable mapping

```python
plan = planner.plan(step)
```

---

### 5. Runtime Adapter

Executes on Fluent:

```python
runtime_adapter.run(method_name, variables)
```

---

### 6. Orchestration (Execution Loop)

Central brain:

```python
result = execution_loop.run(input)
```

Handles:
- TDF sourcing (LLM or library)
- decomposition
- validation
- planning
- execution
- retries (LLM mode)
- state tracking

---

## 🔁 Execution Modes

### 🔹 Library Mode (deterministic, testing)

```python
tdf_mode = "library"
tdf_name = "distribution_mix_incubate"
```

- No retries
- Fail-fast behavior
- Ideal for debugging & validation

---

### 🔹 LLM Mode (adaptive)

```python
tdf_mode = "llm"
```

- Generates workflows dynamically
- Uses validation feedback loop
- Enables self-correcting execution

---

## 🧠 Data Flow Summary

| Stage        | Input        | Output            |
|--------------|-------------|-------------------|
| LLM          | IFU         | TDF               |
| Decomposer   | TDF         | Workflow          |
| Validation   | Workflow    | Validated workflow|
| Planner      | Step        | Plan              |
| Runtime      | Plan        | Execution         |
| State        | Step        | Updated state     |

---

## 🧠 Design Principles

### 1. Separation of Concerns
Each module has a clear responsibility:
- LLM → interpretation
- Validation → safety
- Planner → optimization
- Runtime → execution

---

### 2. Registry-Driven Logic
All decisions are grounded in explicit system capabilities.

---

### 3. Deterministic Execution (Library Mode)
Same input → same execution

---

### 4. Self-Correcting Loop (LLM Mode)

```text
LLM → Validation → Feedback → LLM → Improved Output
```

---

### 5. Explainability
Planner decisions are traceable and debuggable.

---

## 🚀 What Makes This System Different

This system behaves like a **compiler for lab automation**:

```text
IFU → Intermediate Representation → Optimized Plan → Execution
```

Where:
- IFU = source code
- TDF = IR
- Registry = constraints
- Planner = optimizer
- Runtime = executor

---

## 🧪 Minimal Execution Example

```python
result = execution_loop.run(ifu_text)

if result.success:
    print("Execution completed")
else:
    print(result.error)
```

---

## 🔮 Future Extensions

- Advanced planner (multi-objective optimization)
- Execution feedback loop (closed-loop learning)
- SDK / API productization
- UI layer for workflow design
- Multi-instrument orchestration

---

## 📌 Summary

The `execution_engine` turns:

```text
Human intent → Structured → Validated → Optimized → Executed
```

into real-world lab automation — safely, transparently, and at scale.
