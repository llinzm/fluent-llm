# 🔄 Orchestration — End-to-End Execution Engine

## 🎯 Overview

The `orchestration` package is the **control tower** of the system.

It connects all components into a **closed-loop execution pipeline**:

👉 In short:  
**IFU → Workflow → Validation → Planning → Execution → State**

---

## 🧱 Full Data Flow

IFU (text or predefined TDF)
 ↓
TDF Generation (LLM or Library)
 ↓
Workflow Decomposition
 ↓
Validation
 ↓
(Optional Retry Loop)
 ↓
(Optional Simulation)
 ↓
Planning (step-by-step)
 ↓
Runtime Execution
 ↓
State Update
 ↓
Execution Result

---

## 🧩 Modules

### 1. execution_loop.py (Core Orchestrator)

Main entry point.

```python
result = execution_loop.run(ifu_text)
```

Responsibilities:
- Coordinates all subsystems
- Manages retry logic
- Tracks execution logs
- Handles failure modes

See implementation

---

### 2. tdf_library.py

Provides **predefined workflows (TDFs)** for testing and deterministic runs.

```python
from execution_engine.orchestration.tdf_library import distribution_mix_incubate

tdf = distribution_mix_incubate()
```

Examples available 
- simple_distribution
- distribution_with_incubation
- distribution_mix_incubate

---

## ⚙️ Execution Modes

### 1. Library Mode (Deterministic)

```python
execution_loop = ExecutionLoop(
    ...,
    tdf_mode="library",
    tdf_name="distribution_mix_incubate"
)
```

- No LLM
- No retries
- Fast debugging

---

### 2. LLM Mode (Dynamic)

```python
execution_loop = ExecutionLoop(
    ...,
    tdf_mode="llm"
)
```

- IFU → TDF via LLM
- Supports retry loop via validation feedback

---

## 🔁 Retry Logic

When validation fails:

```text
Validation → Feedback → Retry Prompt → LLM → New TDF
```

BUT:

```python
if tdf_mode == "library":
    # fail fast (no retry)
```

---

## ⚙️ Step-by-Step Execution

### 1. TDF Generation

```python
generated_tdf = self.llm.generate_tdf(prompt)
# OR
generated_tdf = tdf_library.<name>()
```

---

### 2. Workflow Decomposition

```python
workflow = decomposer.decompose(generated_tdf)
```

---

### 3. Validation

```python
result = validator.validate_workflow(workflow)
```

---

### 4. Planning

```python
plan = planner.plan(step)
```

---

### 5. Execution

```python
runtime_adapter.run_method(plan.method_name, plan.variables)
```

---

### 6. State Update

```python
state_manager.update(step)
```

---

## 🧪 Minimal Example

```python
from execution_engine.orchestration.execution_loop import ExecutionLoop

loop = ExecutionLoop(
    llm=None,
    decomposer=decomposer,
    validator=validator,
    feedback_builder=feedback_builder,
    planner=planner,
    runtime_adapter=adapter,
    state_manager=state_manager,
    tdf_mode="library",
    tdf_name="simple_distribution"
)

result = loop.run("Distribute buffer")

print(result.success)
print(result.execution_log)
```

---

## 📊 Execution Result

```python
ExecutionLoopResult(
    success=True,
    attempts=1,
    plans=[...],
    execution_log=[...],
    state=...
)
```

Key fields:
- success
- attempts
- workflow
- plans
- execution_log
- error


---

## 🧠 Key Concepts

### 1. Central Orchestration

This is the only place where:
- validation
- planning
- execution

are combined

---

### 2. Fail-Fast vs Retry

| Mode | Behavior |
|------|--------|
| library | fail fast |
| llm | retry with feedback |

---

### 3. Observability

Execution log tracks every stage:

```python
{
    "stage": "plan",
    "step_index": 0,
    "status": "ok"
}
```

---

### 4. Loose Coupling

Each component is injected:

```python
ExecutionLoop(
    llm=...,
    planner=...,
    validator=...
)
```

👉 Enables testing and modular upgrades

---

## 🚀 Future Improvements

- Parallel execution of independent steps
- Smarter retry strategies (partial fixes)
- Execution-time feedback into planner
- Real-time monitoring UI
- Persistent state/history

---

## 📌 Summary

The orchestration layer is the **brain of the system**:

```text
Input → Validate → Plan → Execute → Track → Return
```

It turns individual modules into a **working intelligent pipeline**.
