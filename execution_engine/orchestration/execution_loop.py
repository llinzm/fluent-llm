from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from execution_engine.models.plan import Plan
from execution_engine.models.state import State


@dataclass
class ExecutionLoopResult:
    success: bool
    workflow: Optional[Any] = None
    plans: List[Plan] = field(default_factory=list)
    validation_feedback: Optional[Any] = None
    retry_prompt: Optional[str] = None
    state: Optional[State] = None
    execution_log: List[Dict[str, Any]] = field(default_factory=list)


class ExecutionLoop:
    """
    Integrated orchestration loop that wires together:
    - workflow decomposition
    - workflow validation
    - planner-based method selection
    - runtime execution
    - state updates
    - feedback generation for LLM retries

    Expected collaborator interfaces:

    decomposer:
        decompose(assay) -> Workflow

    validator:
        validate_workflow(workflow) -> ValidationResult

    feedback_builder:
        build_feedback(validation_result) -> ValidationFeedback
        build_retry_prompt(validation_result, original_format="JSON") -> str

    planner:
        plan(step) -> dict or Plan

    runtime_adapter:
        run_method(method_name, variables) -> Any

    state_manager:
        update(step) -> None
        or expose .state / State-compatible fields
    """

    def __init__(
        self,
        decomposer,
        validator,
        feedback_builder,
        planner,
        runtime_adapter,
        state_manager,
        original_format: str = "JSON",
        stop_on_execution_error: bool = True,
    ):
        self.decomposer = decomposer
        self.validator = validator
        self.feedback_builder = feedback_builder
        self.planner = planner
        self.runtime_adapter = runtime_adapter
        self.state_manager = state_manager
        self.original_format = original_format
        self.stop_on_execution_error = stop_on_execution_error

    def run(self, assay) -> ExecutionLoopResult:
        # 1) Decompose high-level assay into linear workflow
        workflow = self.decomposer.decompose(assay)

        # 2) Validate decomposed workflow before planning/execution
        validation_result = self.validator.validate_workflow(workflow)
        if not validation_result.valid:
            return ExecutionLoopResult(
                success=False,
                workflow=workflow,
                validation_feedback=self.feedback_builder.build_feedback(validation_result),
                retry_prompt=self.feedback_builder.build_retry_prompt(
                    validation_result, original_format=self.original_format
                ),
                state=self._extract_state(),
            )

        # 3) Plan + execute each step in order
        plans: List[Plan] = []
        execution_log: List[Dict[str, Any]] = []

        for index, step in enumerate(workflow.steps):
            raw_plan = self.planner.plan(step)
            plan = self._normalize_plan(raw_plan)
            plans.append(plan)

            try:
                runtime_result = self.runtime_adapter.run_method(
                    plan.method_name,
                    plan.variables,
                )

                execution_log.append(
                    {
                        "step_index": index,
                        "step_type": getattr(step, "type", None),
                        "method_name": plan.method_name,
                        "variables": plan.variables,
                        "runtime_result": runtime_result,
                        "status": "executed",
                    }
                )

                # Update state only after successful execution of the step
                self.state_manager.update(step)

            except Exception as exc:
                execution_log.append(
                    {
                        "step_index": index,
                        "step_type": getattr(step, "type", None),
                        "method_name": plan.method_name,
                        "variables": plan.variables,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

                if self.stop_on_execution_error:
                    return ExecutionLoopResult(
                        success=False,
                        workflow=workflow,
                        plans=plans,
                        state=self._extract_state(),
                        execution_log=execution_log,
                    )

        return ExecutionLoopResult(
            success=True,
            workflow=workflow,
            plans=plans,
            state=self._extract_state(),
            execution_log=execution_log,
        )

    def _normalize_plan(self, raw_plan) -> Plan:
        if isinstance(raw_plan, Plan):
            return raw_plan

        return Plan(
            method_name=raw_plan["method_name"],
            variables=raw_plan["variables"],
            score=raw_plan.get("score", 0.0),
            reasoning=raw_plan.get("reasoning", {}),
        )

    def _extract_state(self):
        if isinstance(self.state_manager, State):
            return self.state_manager
        if hasattr(self.state_manager, "state"):
            return self.state_manager.state
        return self.state_manager
