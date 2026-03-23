
from execution_engine.models.plan import Plan

def test_plan_structure():
    p = Plan(method_name="test", variables={"a":1}, score=1.0, reasoning={})
    assert p.method_name == "test"
    assert p.score == 1.0
