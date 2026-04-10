from execution_engine.models.workflow import STEP_SCHEMA, Step, Workflow

def test_workflow_creation():
    wf = Workflow(steps=[Step(type="get_tips", params={"diti_type": "FCA_DiTi_200uL"})])
    assert len(wf.steps) == 1
    assert wf.steps[0].type == "get_tips"

def test_step_schema_uses_required_optional_structure():
    schema = STEP_SCHEMA["sample_transfer"]
    assert "required" in schema
    assert "optional" in schema
    assert "labware_source" in schema["required"]
    assert "number_replicates" in schema["optional"]

def test_mix_volume_schema_exists():
    schema = STEP_SCHEMA["mix_volume"]
    assert schema["required"] == ["labware", "volumes"]
    assert "cycles" in schema["optional"]
