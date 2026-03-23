# Orchestration Module

## Purpose

This module wires together the core execution stack:

1. **Workflow decomposition**
2. **Validation**
3. **Feedback generation for LLM retries**
4. **Planning**
5. **Runtime execution**
6. **State updates**

## Main flow

```python
result = execution_loop.run(assay)
```

### Success path
- assay -> workflow
- workflow validates
- each step is planned
- each plan is executed via runtime adapter
- workflow state is updated after each successful step

### Failure path
If workflow validation fails:
- return structured validation feedback
- return an LLM-ready retry prompt

If runtime execution fails:
- stop immediately (configurable)
- return execution log

## Why this matters

This is the first place where:
- models
- workflow layer
- planner
- validation
- runtime

all work together as one system.
