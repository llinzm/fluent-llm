from execution_engine.models.plan import Plan

def test_plan_creation():
    plan = Plan(
        method_name="ReagentDistribution",
        variables={"volume_uL": 50},
        score=1.0,
        reasoning={"coverage": 1.0},
    )
    assert plan.method_name == "ReagentDistribution"
    assert plan.variables["volume_uL"] == 50
