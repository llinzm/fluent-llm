from execution_engine.workflow.decomposer import WorkflowDecomposer
from execution_engine.models.workflow import Step

class MockAssay:
    def __init__(self, steps):
        self.steps = steps

def test_serial_dilution():
    d = WorkflowDecomposer()
    assay = MockAssay([Step(type="serial_dilution", params={})])
    wf = d.decompose(assay)
    types = [s.type for s in wf.steps]
    assert len(types) == 4
    assert "fill_plate" in types

def test_trbc():
    d = WorkflowDecomposer()
    assay = MockAssay([Step(type="add_trbc", params={})])
    wf = d.decompose(assay)
    assert [s.type for s in wf.steps] == ["mix_trbc", "distribute_trbc"]
