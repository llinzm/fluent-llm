from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


class RuntimeAdapterError(Exception):
    """Raised when execution through the PyFluent layer fails."""
    pass


@dataclass
class ExecutionResult:
    success: bool
    method_name: str
    variables: Dict[str, Any]
    raw_result: Any = None


class PyFluentAdapter:
    """
    Concrete runtime adapter for Fluent execution through the PyFluent layer.

    Supports two integration modes:

    1. Runtime mode
       Calls methods directly on a runtime-like object:
         - PrepareMethod(method_name)
         - SetVariableValue(name, value)
         - RunMethod()

    2. MethodManager mode
       Uses a higher-level PyFluent method manager if available:
         - run_method(method_name=..., variables=...)

    The adapter prefers MethodManager mode when a method_manager is provided.
    """

    def __init__(
        self,
        runtime: Optional[Any] = None,
        method_manager: Optional[Any] = None,
        strict_variables: bool = True,
    ) -> None:
        self.runtime = runtime
        self.method_manager = method_manager
        self.strict_variables = strict_variables

        if self.runtime is None and self.method_manager is None:
            raise RuntimeAdapterError(
                "PyFluentAdapter requires either a runtime or a method_manager."
            )

    def run_method(self, method_name: str, variables: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """
        Execute a FluentControl method through PyFluent.
        """
        if not method_name or not isinstance(method_name, str):
            raise RuntimeAdapterError("method_name must be a non-empty string.")

        variables = variables or {}
        self._validate_variables(variables)

        try:
            if self.method_manager is not None:
                raw = self._run_via_method_manager(method_name, variables)
            else:
                raw = self._run_via_runtime(method_name, variables)

            return ExecutionResult(
                success=True,
                method_name=method_name,
                variables=variables,
                raw_result=raw,
            )
        except Exception as exc:
            raise RuntimeAdapterError(
                f"PyFluent execution failed for method '{method_name}': {exc}"
            ) from exc

    def _run_via_method_manager(self, method_name: str, variables: Dict[str, Any]) -> Any:
        if not hasattr(self.method_manager, "run_method"):
            raise RuntimeAdapterError("Provided method_manager has no run_method().")

        return self.method_manager.run_method(
            method_name=method_name,
            variables=variables,
        )

    def _run_via_runtime(self, method_name: str, variables: Dict[str, Any]) -> Any:
        required_methods = ["PrepareMethod", "SetVariableValue", "RunMethod"]
        missing = [m for m in required_methods if not hasattr(self.runtime, m)]
        if missing:
            raise RuntimeAdapterError(
                f"Runtime object missing required methods: {missing}"
            )

        self.runtime.PrepareMethod(method_name)

        for name, value in variables.items():
            self.runtime.SetVariableValue(name, value)

        return self.runtime.RunMethod()

    def _validate_variables(self, variables: Dict[str, Any]) -> None:
        if not isinstance(variables, dict):
            raise RuntimeAdapterError("variables must be a dictionary.")

        for key, value in variables.items():
            if not isinstance(key, str) or not key:
                raise RuntimeAdapterError("All variable names must be non-empty strings.")

            if self.strict_variables and value is None:
                raise RuntimeAdapterError(
                    f"Variable '{key}' has value None, which is not allowed in strict mode."
                )
