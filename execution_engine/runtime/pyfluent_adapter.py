from __future__ import annotations

from typing import Any, Dict, Protocol

from execution_engine.models.plan import ExecutionPlan


class PyFluentRuntime(Protocol):
    def PrepareMethod(self, method_name: str) -> None: ...
    def SetVariableValue(self, name: str, value: Any) -> None: ...
    def RunMethod(self) -> None: ...


class PyFluentAdapter:
    def __init__(self, runtime: PyFluentRuntime) -> None:
        self.runtime = runtime

    def run_method(self, method_name: str, variables: Dict[str, Any]) -> bool:
        self.runtime.PrepareMethod(method_name)
        for name, value in variables.items():
            self.runtime.SetVariableValue(name, value)
        self.runtime.RunMethod()
        return True

    def execute_plan(self, plan: ExecutionPlan) -> bool:
        return self.run_method(plan.method_name, plan.variables)
