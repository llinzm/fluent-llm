# Runtime Module — PyFluent Adapter

## Purpose

This module is the concrete execution bridge between the `execution_engine`
and the PyFluent / FluentControl runtime layer.

It is responsible for taking a planned method invocation:

- `method_name`
- `variables`

and executing it against FluentControl through PyFluent.

## Why this module exists

The planner should decide **what** to run.
The runtime adapter should decide **how** to run it.

This separation keeps the architecture clean:

- planner = execution intelligence
- runtime adapter = execution mechanics

## Supported execution modes

### 1. MethodManager mode
Uses a higher-level PyFluent `MethodManager`-style API:

```python
method_manager.run_method(method_name="MyMethod", variables={...})
```

### 2. Runtime mode
Uses a low-level Fluent runtime-like API:

```python
runtime.PrepareMethod(method_name)
runtime.SetVariableValue(name, value)
runtime.RunMethod()
```

The adapter prefers MethodManager mode if available.

## Minimal example

```python
from execution_engine.runtime import PyFluentAdapter

runtime = my_runtime_connection

adapter = PyFluentAdapter(runtime=runtime)

result = adapter.run_method(
    "ReagentDistribution_With_Incubation",
    {
        "SOURCE_LABWARE": "Trough_100mL",
        "DEST_LABWARE": "Plate_96",
        "VOLUME_UL": 50,
    }
)

print(result.success)
print(result.method_name)
```

## Design notes

- validates method name and variables
- raises `RuntimeAdapterError` on failures
- can run with either a `runtime` or a `method_manager`
- isolates Fluent-specific execution from the rest of the system
