"""
End-to-End Execution Engine Demo (FluentControl connected)
This is a demo of the execution engine connected to a FluentControl runtime.
"""
from dotenv import load_dotenv
import os

load_dotenv()

from execution_engine.llm import LLMClient
from execution_engine.workflow.decomposer import WorkflowDecomposer
from execution_engine.validation.validator_wrapper import ValidatorWrapper
from execution_engine.validation.feedback_builder import FeedbackBuilder
from execution_engine.planner.planner import Planner
from execution_engine.runtime import PyFluentAdapter
from execution_engine.orchestration import ExecutionLoop


# --------------------------------------------------
# REAL RUNTIME (replace with actual Fluent connection)
# --------------------------------------------------

class FluentRuntime:
    """
    This should wrap your real FluentControl runtime object.
    Replace internals with actual PyFluent / COM connection.
    """

    def __init__(self):
        # TODO: connect to FluentControl
        # e.g. VisionX API / COM / PyFluent runtime
        # The real integration is:
        # fluent_runtime = YOUR_REAL_RUNTIME_OBJECT
        # runtime_adapter = PyFluentAdapter(runtime=fluent_runtime)
        pass

    def PrepareMethod(self, method_name):
        print(f"[Fluent] Preparing method: {method_name}")
        # real call here

    def SetVariableValue(self, name, value):
        print(f"[Fluent] Set {name} = {value}")
        # real call here

    def RunMethod(self):
        print("[Fluent] Running method...")
        # real call here
        return {"status": "ok"}


# --------------------------------------------------
# STATE MANAGER (unchanged)
# --------------------------------------------------

class DemoStateManager:
    def __init__(self):
        self.executed_steps = []

    def update(self, step):
        self.executed_steps.append(step.type)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    ifu_text = """
    Distribute 50 µL of DPBS buffer into a 96-well plate.
    Then incubate for 10 minutes.
    """

    # --------------------------------------------------
    # REGISTRY (use your real one later)
    # --------------------------------------------------

    from execution_engine.capability_registry import loader


    registry = loader.load_default_registry()  # or your loader

    # --------------------------------------------------
    # COMPONENTS
    # --------------------------------------------------

    llm = LLMClient(provider="openai", model="gpt-4o-mini", max_retries=3)
    decomposer = WorkflowDecomposer()
    validator = ValidatorWrapper(registry)
    feedback_builder = FeedbackBuilder()
    planner = Planner(registry, enable_liquid_inference=True)

    # 🔥 REAL RUNTIME CONNECTION
    fluent_runtime = FluentRuntime()
    runtime_adapter = PyFluentAdapter(runtime=fluent_runtime)

    state_manager = DemoStateManager()

    # --------------------------------------------------
    # EXECUTION LOOP (UNCHANGED)
    # --------------------------------------------------

    loop = ExecutionLoop(
        llm=llm,
        decomposer=decomposer,
        validator=validator,
        feedback_builder=feedback_builder,
        planner=planner,
        runtime_adapter=runtime_adapter,
        state_manager=state_manager,
        max_retries=2,
        tdf_mode="library",
        tdf_name="distribution_mix_incubate"
    )

     # --------------------------------------------------
    # RUN (WITH DEBUGGING)
    # --------------------------------------------------

    import traceback

    try:
        result = loop.run(ifu_text)

    except Exception as e:
        print("\n🚨 HARD FAILURE DURING EXECUTION LOOP 🚨")
        traceback.print_exc()
        raise

    print("\n=== FINAL RESULT ===")
    print(f"success: {result.success}")
    print(f"attempts: {result.attempts}")
    print(f"plans: {len(result.plans)}")
    print(f"execution log entries: {len(result.execution_log)}")

    if result.error:
        print(f"\n❌ error: {result.error}")

    if result.retry_prompt:
        print("\n🔁 Retry prompt:")
        print(result.retry_prompt)


if __name__ == "__main__":
    main()