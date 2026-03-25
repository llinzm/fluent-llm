import pytest

from execution_engine.runtime.pyfluent_adapter import (
    PyFluentAdapter,
    RuntimeAdapterError,
    ExecutionResult,
)


class MockRuntime:
    def __init__(self):
        self.calls = []

    def PrepareMethod(self, method_name):
        self.calls.append(("PrepareMethod", method_name))

    def SetVariableValue(self, name, value):
        self.calls.append(("SetVariableValue", name, value))

    def RunMethod(self):
        self.calls.append(("RunMethod",))
        return {"status": "ok"}


class MockMethodManager:
    def __init__(self):
        self.calls = []

    def run_method(self, method_name=None, variables=None):
        self.calls.append((method_name, variables))
        return {"status": "ok", "method_name": method_name}


def test_runtime_mode_executes_expected_sequence():
    runtime = MockRuntime()
    adapter = PyFluentAdapter(runtime=runtime)

    result = adapter.run_method(
        "ExampleMethod",
        {"A": 1, "B": 2},
    )

    assert isinstance(result, ExecutionResult)
    assert result.success is True
    assert result.method_name == "ExampleMethod"
    assert runtime.calls == [
        ("PrepareMethod", "ExampleMethod"),
        ("SetVariableValue", "A", 1),
        ("SetVariableValue", "B", 2),
        ("RunMethod",),
    ]


def test_method_manager_mode_is_preferred_when_present():
    runtime = MockRuntime()
    mm = MockMethodManager()
    adapter = PyFluentAdapter(runtime=runtime, method_manager=mm)

    result = adapter.run_method("MyMethod", {"X": 42})

    assert result.success is True
    assert mm.calls == [("MyMethod", {"X": 42})]
    assert runtime.calls == []


def test_rejects_empty_method_name():
    runtime = MockRuntime()
    adapter = PyFluentAdapter(runtime=runtime)

    with pytest.raises(RuntimeAdapterError):
        adapter.run_method("", {"A": 1})


def test_rejects_non_dict_variables():
    runtime = MockRuntime()
    adapter = PyFluentAdapter(runtime=runtime)

    with pytest.raises(RuntimeAdapterError):
        adapter.run_method("ExampleMethod", ["bad", "variables"])


def test_rejects_none_variable_in_strict_mode():
    runtime = MockRuntime()
    adapter = PyFluentAdapter(runtime=runtime, strict_variables=True)

    with pytest.raises(RuntimeAdapterError):
        adapter.run_method("ExampleMethod", {"A": None})


def test_allows_none_variable_when_not_strict():
    runtime = MockRuntime()
    adapter = PyFluentAdapter(runtime=runtime, strict_variables=False)

    result = adapter.run_method("ExampleMethod", {"A": None})

    assert result.success is True
    assert ("SetVariableValue", "A", None) in runtime.calls


def test_requires_runtime_or_method_manager():
    with pytest.raises(RuntimeAdapterError):
        PyFluentAdapter()


def test_wraps_runtime_failure():
    class FailingRuntime(MockRuntime):
        def RunMethod(self):
            raise RuntimeError("boom")

    adapter = PyFluentAdapter(runtime=FailingRuntime())

    with pytest.raises(RuntimeAdapterError) as exc:
        adapter.run_method("BadMethod", {"A": 1})

    assert "PyFluent execution failed" in str(exc.value)
