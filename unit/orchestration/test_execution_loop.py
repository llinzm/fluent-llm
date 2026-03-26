from execution_engine.models.feedback import FeedbackItem, ValidationFeedback
from execution_engine.models.workflow import Step, Workflow
from execution_engine.orchestration.execution_loop import ExecutionLoop


class MockLLM:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = 0

    def generate_tdf(self, text):
        out = self.outputs[self.calls]
        self.calls += 1
        return out


class MockDecomposer:
    def decompose(self, tdf):
        steps = [Step(type=s["type"], params=s.get("params", {})) for s in tdf["steps"]]
        return Workflow(steps=steps)


class MockValidationResult:
    def __init__(self, valid=True):
        self.valid = valid

    def to_feedback(self):
        return ValidationFeedback(
            errors=[
                FeedbackItem(
                    type="missing_required_field",
                    message="Missing required field",
                    suggestion=["Add source"],
                    context={"step_type": "reagent_distribution"},
                    severity="error",
                )
            ] if not self.valid else [],
            warnings=[],
        )


class MockValidator:
    def __init__(self, valid_sequence):
        self.valid_sequence = valid_sequence
        self.calls = 0

    def validate_workflow(self, workflow):
        valid = self.valid_sequence[self.calls]
        self.calls += 1
        return MockValidationResult(valid=valid)


class MockFeedbackBuilder:
    def build_feedback(self, validation_result):
        return validation_result.to_feedback()

    def build_retry_prompt(self, validation_result, original_format="JSON"):
        return f"Retry in {original_format}"


class MockPlanner:
    def plan(self, step):
        return {
            "method_name": f"Method_{step.type}",
            "variables": {"step_type": step.type},
            "score": 1.0,
            "reasoning": {"coverage": 1.0},
        }


class MockRuntimeResult:
    def __init__(self, success=True):
        self.success = success
        self.raw_result = {"ok": success}


class MockRuntimeAdapter:
    def __init__(self, fail_on_method=None):
        self.fail_on_method = fail_on_method
        self.calls = []

    def run_method(self, method_name, variables):
        self.calls.append((method_name, variables))
        if method_name == self.fail_on_method:
            raise RuntimeError("runtime failure")
        return MockRuntimeResult(success=True)


class MockStateManager:
    def __init__(self):
        self.executed_steps = []

    def update(self, step):
        self.executed_steps.append(step.type)


class MockSimulator:
    def __init__(self, success=True):
        self.success = success

    def simulate(self, workflow):
        return {"success": self.success, "checked_steps": len(workflow.steps)}


def test_execution_loop_success_path():
    llm = MockLLM(outputs=[{"steps": [{"type": "fill_plate", "params": {}}, {"type": "incubate", "params": {}}]}])

    runtime = MockRuntimeAdapter()
    state = MockStateManager()

    loop = ExecutionLoop(
        llm=llm,
        decomposer=MockDecomposer(),
        validator=MockValidator(valid_sequence=[True]),
        feedback_builder=MockFeedbackBuilder(),
        planner=MockPlanner(),
        runtime_adapter=runtime,
        state_manager=state,
        simulator=MockSimulator(success=True),
    )

    result = loop.run("test IFU")

    assert result.success is True
    assert result.attempts == 1
    assert len(result.plans) == 2
    assert len(result.execution_log) >= 5
    assert state.executed_steps == ["fill_plate", "incubate"]


def test_execution_loop_retries_after_validation_failure():
    llm = MockLLM(outputs=[
        {"steps": [{"type": "reagent_distribution", "params": {}}]},
        {"steps": [{"type": "incubate", "params": {}}]},
    ])

    loop = ExecutionLoop(
        llm=llm,
        decomposer=MockDecomposer(),
        validator=MockValidator(valid_sequence=[False, True]),
        feedback_builder=MockFeedbackBuilder(),
        planner=MockPlanner(),
        runtime_adapter=MockRuntimeAdapter(),
        state_manager=MockStateManager(),
        simulator=MockSimulator(success=True),
        max_retries=2,
    )

    result = loop.run("test IFU")
    assert result.success is True
    assert result.attempts == 2


def test_execution_loop_returns_failure_after_max_retries():
    llm = MockLLM(outputs=[
        {"steps": [{"type": "reagent_distribution", "params": {}}]},
        {"steps": [{"type": "reagent_distribution", "params": {}}]},
        {"steps": [{"type": "reagent_distribution", "params": {}}]},
    ])

    loop = ExecutionLoop(
        llm=llm,
        decomposer=MockDecomposer(),
        validator=MockValidator(valid_sequence=[False, False, False]),
        feedback_builder=MockFeedbackBuilder(),
        planner=MockPlanner(),
        runtime_adapter=MockRuntimeAdapter(),
        state_manager=MockStateManager(),
        simulator=MockSimulator(success=True),
        max_retries=2,
    )

    result = loop.run("test IFU")
    assert result.success is False
    assert "Validation failed" in result.error


def test_execution_loop_stops_on_simulation_failure():
    llm = MockLLM(outputs=[{"steps": [{"type": "fill_plate", "params": {}}]}])

    loop = ExecutionLoop(
        llm=llm,
        decomposer=MockDecomposer(),
        validator=MockValidator(valid_sequence=[True]),
        feedback_builder=MockFeedbackBuilder(),
        planner=MockPlanner(),
        runtime_adapter=MockRuntimeAdapter(),
        state_manager=MockStateManager(),
        simulator=MockSimulator(success=False),
    )

    result = loop.run("test IFU")
    assert result.success is False
    assert result.error == "Simulation failed"


def test_execution_loop_stops_on_runtime_error():
    llm = MockLLM(outputs=[{"steps": [{"type": "fill_plate", "params": {}}]}])

    state = MockStateManager()

    loop = ExecutionLoop(
        llm=llm,
        decomposer=MockDecomposer(),
        validator=MockValidator(valid_sequence=[True]),
        feedback_builder=MockFeedbackBuilder(),
        planner=MockPlanner(),
        runtime_adapter=MockRuntimeAdapter(fail_on_method="Method_fill_plate"),
        state_manager=state,
        simulator=MockSimulator(success=True),
    )

    result = loop.run("test IFU")
    assert result.success is False
    assert "Execution failed" in result.error
    assert state.executed_steps == []
