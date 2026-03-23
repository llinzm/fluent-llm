from dataclasses import dataclass

from execution_engine.models.feedback import FeedbackItem, ValidationFeedback
from execution_engine.models.workflow import Step, Workflow
from execution_engine.orchestration.execution_loop import ExecutionLoop


class MockAssay:
    def __init__(self, steps):
        self.steps = steps


class MockDecomposer:
    def decompose(self, assay):
        return Workflow(steps=assay.steps)


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
    def __init__(self, valid=True):
        self.valid = valid

    def validate_workflow(self, workflow):
        return MockValidationResult(valid=self.valid)


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


class MockRuntimeAdapter:
    def __init__(self, fail_on_method=None):
        self.fail_on_method = fail_on_method
        self.calls = []

    def run_method(self, method_name, variables):
        self.calls.append((method_name, variables))
        if method_name == self.fail_on_method:
            raise RuntimeError("runtime failure")
        return {"ok": True, "method_name": method_name}


class MockStateManager:
    def __init__(self):
        self.executed_steps = []

    def update(self, step):
        self.executed_steps.append(step.type)


def test_execution_loop_success_path():
    assay = MockAssay([
        Step(type="fill_plate", params={"volumes": {"A1": 50}}),
        Step(type="incubate", params={}),
    ])

    runtime = MockRuntimeAdapter()
    state = MockStateManager()

    loop = ExecutionLoop(
        decomposer=MockDecomposer(),
        validator=MockValidator(valid=True),
        feedback_builder=MockFeedbackBuilder(),
        planner=MockPlanner(),
        runtime_adapter=runtime,
        state_manager=state,
    )

    result = loop.run(assay)

    assert result.success is True
    assert len(result.plans) == 2
    assert len(runtime.calls) == 2
    assert state.executed_steps == ["fill_plate", "incubate"]
    assert result.retry_prompt is None


def test_execution_loop_returns_feedback_on_validation_failure():
    assay = MockAssay([
        Step(type="reagent_distribution", params={"volume_uL": 50}),
    ])

    loop = ExecutionLoop(
        decomposer=MockDecomposer(),
        validator=MockValidator(valid=False),
        feedback_builder=MockFeedbackBuilder(),
        planner=MockPlanner(),
        runtime_adapter=MockRuntimeAdapter(),
        state_manager=MockStateManager(),
    )

    result = loop.run(assay)

    assert result.success is False
    assert result.validation_feedback is not None
    assert result.retry_prompt == "Retry in JSON"
    assert result.plans == []


def test_execution_loop_stops_on_runtime_error():
    assay = MockAssay([
        Step(type="fill_plate", params={}),
        Step(type="incubate", params={}),
    ])

    runtime = MockRuntimeAdapter(fail_on_method="Method_incubate")
    state = MockStateManager()

    loop = ExecutionLoop(
        decomposer=MockDecomposer(),
        validator=MockValidator(valid=True),
        feedback_builder=MockFeedbackBuilder(),
        planner=MockPlanner(),
        runtime_adapter=runtime,
        state_manager=state,
        stop_on_execution_error=True,
    )

    result = loop.run(assay)

    assert result.success is False
    assert len(result.execution_log) == 2
    assert result.execution_log[-1]["status"] == "failed"
    # state only updated for the successful first step
    assert state.executed_steps == ["fill_plate"]
