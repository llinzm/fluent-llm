import pytest
from execution_engine.workflow.dependency_resolver import DependencyResolver
from execution_engine.models.workflow import Workflow, Step

def test_valid():
    r = DependencyResolver()
    wf = Workflow(steps=[Step("fill_plate"), Step("add_antigen"), Step("mix")])
    assert r.validate(wf)

def test_invalid():
    r = DependencyResolver()
    wf = Workflow(steps=[Step("mix")])
    with pytest.raises(Exception):
        r.validate(wf)
