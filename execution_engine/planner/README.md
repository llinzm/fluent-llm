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

Inside `plan(step)`, the first thing that happens is:

```python
candidates = self.selector.select(step)
```
That means CandidateSelector is responsible for:

looking through the methods in the capability registry
keeping only methods whose supports list contains the current step.type
applying hard constraints like tip existence, volume fit, and liquid/tip compatibility

So its job is: “which methods are even allowed for this step?”

---

### 3. scoring.py

Still inside plan(step), the planner then loops over those candidates and does:

```python
result = self.scorer.score(step, method)
```
This score combines several factors:

- coverage
- whether a tip is specified
- whether a volume is present
- whether a liquid class is present
- efficiency
- risk penalty if the requested volume exceeds tip capacity

So its job is: “among the allowed methods, which one is best?”


---

### 4. variable_mapper.py

Prepares execution variables. Once the best method is chosen, planner does:

```python
variables = mapper.map(step, method)
```
This produces the dict that is sent to the runtime adapter for Fluent execution
So its job is: “turn the workflow step into runtime input variables.”

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

Are `candidate_selector.py` and `scoring.py` needed?

Yes.

Without `candidate_selector.py`:

- planner would try to score every registry method, even irrelevant ones
- you would lose hard filtering

Without `scoring.py`:

- planner would only know which methods are valid, not which one is preferable
- you could only pick “first valid candidate,” which is much weaker

So conceptually:

- candidate_selector.py = hard filter
- scoring.py = soft ranking

That separation is actually a good design.


## Planner Algorithm (How it works)

Step → Candidate Selection → Scoring → Mapping → Plan

1. CandidateSelector
Filters registry methods that support the step and satisfy hard constraints.

2. ScoringEngine
Ranks candidates based on completeness, efficiency, and constraints.

3. VariableMapper
Maps step parameters to runtime execution variables.

Final output:
- method_name
- variables
- score

## Design Rationale

- CandidateSelector = hard filter
- ScoringEngine = soft ranking
- VariableMapper = execution mapping
