from execution_engine.models.workflow import Step, Workflow
from execution_engine.validation.validator_wrapper import ValidatorWrapper


class DummyRegistry:
    def __init__(self):
        self.tips = {
            "FCA_DiTi_200uL": {"max_volume_uL": 200, "min_volume_uL": 5},
            "FCA_DiTi_1000uL": {"max_volume_uL": 1000, "min_volume_uL": 50},
        }
        self.liquid_classes = {
            "Water_Free": {"compatible_tip_types": ["FCA_DiTi_200uL", "FCA_DiTi_1000uL"]},
            "Viscous": {"compatible_tip_types": ["FCA_DiTi_1000uL"]},
        }
        self.labware = {
            "types": {
                "Trough_100mL": {},
                "Plate_96": {},
            }
        }

    def get_tip(self, name):
        return self.tips.get(name)

    def get_liquid_class(self, name):
        return self.liquid_classes.get(name)


def test_valid_step_passes():
    registry = DummyRegistry()
    validator = ValidatorWrapper(registry)

    step = Step(
        type="reagent_distribution",
        params={
            "volume_uL": 50,
            "source": "Trough_100mL",
            "target": "Plate_96",
            "tip_type": "FCA_DiTi_200uL",
            "liquid_class": "Water_Free",
        },
    )

    result = validator.validate_step(step)
    assert result.valid is True
    assert result.errors == []


def test_tip_volume_exceeded_fails():
    registry = DummyRegistry()
    validator = ValidatorWrapper(registry)

    step = Step(
        type="reagent_distribution",
        params={
            "volume_uL": 300,
            "source": "Trough_100mL",
            "target": "Plate_96",
            "tip_type": "FCA_DiTi_200uL",
            "liquid_class": "Water_Free",
        },
    )

    result = validator.validate_step(step)
    assert result.valid is False
    assert any(e["type"] == "tip_volume_exceeded" for e in result.errors)


def test_liquid_tip_incompatibility_fails():
    registry = DummyRegistry()
    validator = ValidatorWrapper(registry)

    step = Step(
        type="reagent_distribution",
        params={
            "volume_uL": 100,
            "source": "Trough_100mL",
            "target": "Plate_96",
            "tip_type": "FCA_DiTi_200uL",
            "liquid_class": "Viscous",
        },
    )

    result = validator.validate_step(step)
    assert result.valid is False
    assert any(e["type"] == "liquid_tip_incompatibility" for e in result.errors)


def test_missing_required_fields_fail():
    registry = DummyRegistry()
    validator = ValidatorWrapper(registry)

    step = Step(type="reagent_distribution", params={"volume_uL": 50})
    result = validator.validate_step(step)

    assert result.valid is False
    assert any(e["type"] == "missing_required_field" for e in result.errors)


def test_workflow_validation_aggregates_step_index():
    registry = DummyRegistry()
    validator = ValidatorWrapper(registry)

    workflow = Workflow(steps=[
        Step(type="reagent_distribution", params={"volume_uL": 50}),
        Step(type="mix", params={"target": "Plate_96"}),
    ])

    result = validator.validate_workflow(workflow)
    assert result.valid is False
    assert any("step_index" in e["context"] for e in result.errors)
