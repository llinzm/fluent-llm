from execution_engine.models.state import State

def test_state_defaults():
    state = State()
    assert state.tip_loaded is False
    assert state.well_volumes == {}
