# 🧠 Planner — Execution Strategy Engine

## 🎯 Overview

The `planner` package is the **decision-making layer** of the execution engine.

It transforms a validated **workflow step** into an **executable plan** by:

- Selecting compatible methods from the capability registry
- Scoring candidate methods
- Mapping workflow parameters to runtime variables

👉 In short:  
**Step → Best Method → Executable Plan**

---

## 🧱 Planning Flow

Step
 ↓
Candidate Selection
 ↓
Scoring
 ↓
Best Candidate
 ↓
Variable Mapping
 ↓
Execution Plan

---

## 🧩 Modules

### 1. planner.py (Orchestrator)

Main entry point for planning.

```python
plan = planner.plan(step)
```

---

### 2. candidate_selector.py

Finds compatible methods from the registry.

```python
candidates = selector.select(step)
```

---

### 3. scoring.py

Ranks candidates.

```python
score = scorer.score(candidate, step)
```

---

### 4. variable_mapper.py

Maps step parameters to runtime variables.

```python
variables = mapper.map(step, method)
```

---

## ⚙️ How Planning Works

```python
step = Step(type="reagent_distribution", params={...})

candidates = selector.select(step)
best = max(candidates, key=lambda c: scorer.score(c, step))
variables = mapper.map(step, best)

plan = {
    "method": best.name,
    "device": best.device,
    "variables": variables
}
```

---

## 🧪 Minimal Example

```python
from execution_engine.planner.planner import Planner

planner = Planner(registry)
plan = planner.plan(step)

print(plan.method_name)
print(plan.variables)
```

---

## 🧠 Key Concepts

- Capability-driven (no hardcoding)
- Deterministic output
- Modular (selector / scorer / mapper)
- Fail-fast if no candidates

---

## 📌 Summary

Validated Step → Best Method → Executable Plan
