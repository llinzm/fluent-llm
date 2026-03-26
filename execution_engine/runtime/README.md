# ⚙️ Runtime — Execution Adapter Layer

## 🎯 Overview

The `runtime` package is the **execution bridge** between planning and real lab hardware (Fluent / PyFluent).

It converts a **Plan** into a **real method execution** and returns a structured result.

👉 In short:  
**Plan → Method Execution → Result**

---

## 🧱 Role in the System

Plan (from planner)
 ↓
Runtime Adapter
 ↓
FluentControl / PyFluent
 ↓
ExecutionResult
 ↓
State update (orchestration)

---

## 🧩 Core Module

### pyfluent_adapter.py

Main runtime interface.

```python
result = adapter.run_method(method_name, variables)
```

Responsibilities:
- Validate inputs
- Route execution to correct backend
- Execute Fluent methods
- Return structured results

---

## ⚙️ Execution Modes

### 1. MethodManager Mode (Preferred)

```python
method_manager.run_method(
    method_name="MyMethod",
    variables={...}
)
```

✔ Cleaner  
✔ Higher-level abstraction  
✔ Recommended when available  

---

### 2. Runtime Mode (Low-level)

```python
runtime.PrepareMethod(method_name)
runtime.SetVariableValue(name, value)
runtime.RunMethod()
```

✔ Direct FluentControl control  
✔ More flexibility  
✖ Requires correct runtime object  

---

## ⚙️ Execution Flow

### 1. Validate Input

```python
_validate_variables(variables)
```

Checks:
- variables is a dict
- keys are strings
- no None values (if strict mode)

---

### 2. Select Execution Path

```python
if method_manager:
    use MethodManager
else:
    use Runtime API
```

---

### 3. Execute Method

```python
adapter.run_method(method_name, variables)
```

---

### 4. Return Result

```python
ExecutionResult(
    success=True,
    method_name=method_name,
    variables=variables,
    raw_result=...
)
```

---

## 🧪 Minimal Example

```python
from execution_engine.runtime.pyfluent_adapter import PyFluentAdapter

adapter = PyFluentAdapter(runtime=my_runtime)

result = adapter.run_method(
    "ReagentDistribution",
    {
        "volume_uL": 50,
        "source": "Trough_25mL:A1",
        "target": "Plate_96:A1"
    }
)

print(result.success)
```

---

## ⚠️ Strict Mode (Important)

```python
PyFluentAdapter(strict_variables=True)
```

Prevents invalid execution:

- Rejects None values
- Avoids silent runtime failures

Example error:

```text
Variable 'volume_uL' has value None
```

---

## ❌ Error Handling

All execution errors raise:

```python
RuntimeAdapterError
```

Example:

```text
PyFluent execution failed for method 'ReagentDistribution'
```

---

## 🧠 Key Concepts

### Separation of Concerns

| Layer | Role |
|------|------|
| Planner | WHAT to run |
| Runtime | HOW to run |

---

### Hardware Abstraction

- Planner is hardware-agnostic
- Runtime is hardware-specific

---

### Deterministic Execution

- No inference
- No decision-making
- Pure execution layer

---

### Safety

- Input validation before execution
- Strict mode prevents invalid calls

---

## 🚀 Future Improvements

- Async execution
- Retry policies
- Streaming logs
- Multi-device support
- Simulation fallback

---

## 📌 Summary

The runtime layer is the **final execution step**:

```text
Plan → Execute → Result
```

It ensures that high-level plans become **real, safe hardware actions**.
