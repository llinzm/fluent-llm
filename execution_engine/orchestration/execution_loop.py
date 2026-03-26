from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from execution_engine.models.plan import Plan
from execution_engine.models.state import State
from execution_engine.models.workflow import Workflow, Step


@dataclass
class ExecutionLoopResult:
    """Structured result returned by the orchestration loop."""

    success: bool
    attempts: int = 0
    ifu_text: Optional[str] = None
    tdf: Optional[Dict[str, Any]] = None
    workflow: Optional[Any] = None
    plans: List[Plan] = field(default_factory=list)
    validation_feedback: Optional[Any] = None
    retry_prompt: Optional[str] = None
    simulation_result: Optional[Dict[str, Any]] = None
    state: Optional[Any] = None
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


class ExecutionLoop:
    """
    Rich orchestration layer for end-to-end execution.

    Flow:
      IFU -> LLM -> TDF -> Workflow -> Validation
         -> (Retry if invalid)
         -> Simulation (optional)
         -> Planning
         -> Runtime execution
         -> State update

    This class intentionally keeps orchestration concerns separate from:
    - generation (LLM)
    - decomposition (workflow layer)
    - validation
    - planning
    - runtime execution
    - state management
    """

    def __init__(
        self,
        llm,
        decomposer,
        validator,
        feedback_builder,
        planner,
        runtime_adapter,
        state_manager,
        simulator=None,
        original_format: str = "JSON",
        max_retries: int = 2,
        stop_on_execution_error: bool = True,
        tdf_mode: str = "library",
        tdf_name: str = "simple_distribution",
    ):
        self.llm = llm
        self.decomposer = decomposer
        self.validator = validator
        self.feedback_builder = feedback_builder
        self.planner = planner
        self.runtime_adapter = runtime_adapter
        self.state_manager = state_manager
        self.simulator = simulator
        self.original_format = original_format
        self.max_retries = max_retries
        self.stop_on_execution_error = stop_on_execution_error
        self.tdf_mode = tdf_mode
        self.tdf_name = tdf_name

    def run(self, ifu_text: str) -> ExecutionLoopResult:
        """Run the full closed-loop execution pipeline starting from an IFU string."""
        current_prompt = ifu_text
        attempts = 0

        while attempts <= self.max_retries:
            attempts += 1
            execution_log: List[Dict[str, Any]] = []

            # 1) IFU -> TDF
            try:
                if self.tdf_mode == "library":
                    import execution_engine.orchestration.tdf_library as tdf_library

                    if not hasattr(tdf_library, self.tdf_name):
                        raise ValueError(f"TDF '{self.tdf_name}' not found in library")

                    generated_tdf = getattr(tdf_library, self.tdf_name)()

                elif self.tdf_mode == "llm":
                    generated_tdf = self.llm.generate_tdf(current_prompt)

                else:
                    raise ValueError(f"Unknown tdf_mode: {self.tdf_mode}")

            except Exception as exc:
                return ExecutionLoopResult(
                    success=False,
                    attempts=attempts,
                    ifu_text=ifu_text,
                    error=f"TDF generation failed: {exc}",
                    execution_log=execution_log,
                    state=self._extract_state(),
                )

            execution_log.append({
                "stage": "llm",
                "attempt": attempts,
                "status": "ok",
            })

            # 2) TDF -> Workflow
            try:
                workflow = self.decomposer.decompose(generated_tdf)
            except Exception as exc:
                return ExecutionLoopResult(
                    success=False,
                    attempts=attempts,
                    ifu_text=ifu_text,
                    tdf=generated_tdf,
                    error=f"Workflow decomposition failed: {exc}",
                    execution_log=execution_log,
                    state=self._extract_state(),
                )

            execution_log.append({
                "stage": "decompose",
                "attempt": attempts,
                "status": "ok",
                "step_count": len(getattr(workflow, "steps", [])),
            })

            # 3) Validation
            try:
                validation_result = self.validator.validate_workflow(workflow)
            except Exception as exc:
                return ExecutionLoopResult(
                    success=False,
                    attempts=attempts,
                    ifu_text=ifu_text,
                    tdf=generated_tdf,
                    workflow=workflow,
                    error=f"Validation crashed: {exc}",
                    execution_log=execution_log,
                    state=self._extract_state(),
                )

            if not getattr(validation_result, "valid", False) and not getattr(validation_result, "is_valid", False):

                feedback = self.feedback_builder.build_feedback(validation_result)
                retry_prompt = self.feedback_builder.build_retry_prompt(
                    validation_result,
                    original_format=self.original_format,
                )

                execution_log.append({
                    "stage": "validate",
                    "attempt": attempts,
                    "status": "failed",
                    "error_count": len(getattr(feedback, "errors", [])),
                    "warning_count": len(getattr(feedback, "warnings", [])),
                })

                if self.tdf_mode == "library":
                    return ExecutionLoopResult(
                        success=False,
                        attempts=attempts,
                        ifu_text=ifu_text,
                        tdf=generated_tdf,
                        workflow=workflow,
                        validation_feedback=feedback,
                        retry_prompt=retry_prompt,
                        error="Validation failed (library mode - no retry)",
                        execution_log=execution_log,
                        state=self._extract_state(),
                    )

                # existing retry logic
                if attempts > self.max_retries:
                    return ExecutionLoopResult(...)

                current_prompt = retry_prompt
                continue

            execution_log.append({
                "stage": "validate",
                "attempt": attempts,
                "status": "ok",
            })

            # 4) Simulation (optional)
            simulation_result = None
            if self.simulator is not None:
                try:
                    simulation_result = self.simulator.simulate(workflow)
                except Exception as exc:
                    return ExecutionLoopResult(
                        success=False,
                        attempts=attempts,
                        ifu_text=ifu_text,
                        tdf=generated_tdf,
                        workflow=workflow,
                        error=f"Simulation crashed: {exc}",
                        execution_log=execution_log,
                        state=self._extract_state(),
                    )

                execution_log.append({
                    "stage": "simulate",
                    "attempt": attempts,
                    "status": "ok" if simulation_result.get("success", False) else "failed",
                    "details": simulation_result,
                })

                if not simulation_result.get("success", False):
                    return ExecutionLoopResult(
                        success=False,
                        attempts=attempts,
                        ifu_text=ifu_text,
                        tdf=generated_tdf,
                        workflow=workflow,
                        simulation_result=simulation_result,
                        error="Simulation failed",
                        execution_log=execution_log,
                        state=self._extract_state(),
                    )

            # 5) Planning + Runtime execution
            plans: List[Plan] = []
            for index, step in enumerate(workflow.steps):
                try:
                    raw_plan = self.planner.plan(step)
                    plan = self._normalize_plan(raw_plan)
                    plans.append(plan)
                except Exception as exc:
                    execution_log.append({
                        "stage": "plan",
                        "attempt": attempts,
                        "step_index": index,
                        "step_type": getattr(step, "type", None),
                        "status": "failed",
                        "error": str(exc),
                    })
                    return ExecutionLoopResult(
                        success=False,
                        attempts=attempts,
                        ifu_text=ifu_text,
                        tdf=generated_tdf,
                        workflow=workflow,
                        plans=plans,
                        simulation_result=simulation_result,
                        error=f"Planning failed: {exc}",
                        execution_log=execution_log,
                        state=self._extract_state(),
                    )

                execution_log.append({
                    "stage": "plan",
                    "attempt": attempts,
                    "step_index": index,
                    "step_type": getattr(step, "type", None),
                    "status": "ok",
                    "method_name": plan.method_name,
                    "score": plan.score,
                })

                try:
                    runtime_result = self.runtime_adapter.run_method(
                        plan.method_name,
                        plan.variables,
                    )

                    execution_log.append({
                        "stage": "execute",
                        "attempt": attempts,
                        "step_index": index,
                        "step_type": getattr(step, "type", None),
                        "status": "ok",
                        "method_name": plan.method_name,
                        "runtime_result": getattr(runtime_result, "raw_result", runtime_result),
                    })

                    # Update state only after successful execution
                    self.state_manager.update(step)

                except Exception as exc:
                    execution_log.append({
                        "stage": "execute",
                        "attempt": attempts,
                        "step_index": index,
                        "step_type": getattr(step, "type", None),
                        "status": "failed",
                        "method_name": plan.method_name,
                        "error": str(exc),
                    })

                    if self.stop_on_execution_error:
                        return ExecutionLoopResult(
                            success=False,
                            attempts=attempts,
                            ifu_text=ifu_text,
                            tdf=generated_tdf,
                            workflow=workflow,
                            plans=plans,
                            simulation_result=simulation_result,
                            error=f"Execution failed: {exc}",
                            execution_log=execution_log,
                            state=self._extract_state(),
                        )

            return ExecutionLoopResult(
                success=True,
                attempts=attempts,
                ifu_text=ifu_text,
                tdf=generated_tdf,
                workflow=workflow,
                plans=plans,
                simulation_result=simulation_result,
                execution_log=execution_log,
                state=self._extract_state(),
            )

        return ExecutionLoopResult(
            success=False,
            attempts=attempts,
            ifu_text=ifu_text,
            error="Unknown orchestration failure",
            state=self._extract_state(),
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
