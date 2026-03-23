from execution_engine.workflow.state_manager import WorkflowState
from execution_engine.models.workflow import Step

def test_volume():
    s = WorkflowState()
    step = Step(type="fill_plate", params={"volumes": {"A1": 50}})
    s.update(step)
    assert s.get_volume("A1") == 50

def test_tip():
    s = WorkflowState()
    s.update(Step(type="aspirate"))
    assert s.tip_loaded
    s.update(Step(type="dispense"))
    assert not s.tip_loaded
