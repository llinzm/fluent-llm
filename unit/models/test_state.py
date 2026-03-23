
from execution_engine.models.state import State

def test_state_defaults():
    s = State()
    assert s.tip_loaded is False
    assert s.well_volumes == {}
