
from execution_engine.models.workflow import Step, Workflow

def test_workflow_creation():
    steps = [Step(type="mix"), Step(type="incubate")]
    wf = Workflow(steps=steps)
    assert len(wf.steps) == 2
    assert wf.steps[0].type == "mix"
