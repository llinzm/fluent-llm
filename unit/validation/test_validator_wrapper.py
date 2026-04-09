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
                "sample_plate": {},
                "dilution_plate": {},
                "Liquid_waste": {},
            }
        }

    def get_tip(self, name):
        return self.tips.get(name)

    def get_liquid_class(self, name):
        return self.liquid_classes.get(name)


def test_valid_step_passes_new_schema():
    registry = DummyRegistry()
    validator = ValidatorWrapper(registry)

    workflow = Workflow(
        steps=[
            Step(
                type="sample_transfer",
                params={
                    "labware_source": "sample_plate",
                    "labware_target": "dilution_plate",
                    "volumes": 25,
                    "DiTi_type": "FCA_DiTi_200uL",
                    "liquid_class": "Water_Free",
                },
            )
        ]
    )

    result = validator.validate_workflow(workflow)
    assert result.valid is True
    assert result.errors == []


def test_missing_required_fields_fail():
    registry = DummyRegistry()
    validator = ValidatorWrapper(registry)

    workflow = Workflow(
        steps=[
            Step(type="sample_transfer", params={"volumes": 25})
        ]
    )

    result = validator.validate_workflow(workflow)
    assert result.valid is False
    assert any(e["type"] == "missing_required_field" for e in result.errors)


def test_unknown_step_type_fails():
    registry = DummyRegistry()
    validator = ValidatorWrapper(registry)

    workflow = Workflow(steps=[Step(type="does_not_exist", params={})])
    result = validator.validate_workflow(workflow)

    assert result.valid is False
    assert any(e["type"] == "unknown_step_type" for e in result.errors)


def test_tip_volume_exceeded_fails():
    registry = DummyRegistry()
    validator = ValidatorWrapper(registry)

    step = Step(
        type="aspirate_volume",
        params={
            "labware": "Plate_96",
            "volumes": 300,
            "DiTi_type": "FCA_DiTi_200uL",
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
        type="aspirate_volume",
        params={
            "labware": "Plate_96",
            "volumes": 100,
            "DiTi_type": "FCA_DiTi_200uL",
            "liquid_class": "Viscous",
        },
    )

    result = validator.validate_step(step)
    assert result.valid is False
    assert any(e["type"] == "liquid_tip_incompatibility" for e in result.errors)


def test_labware_alias_fields_are_checked():
    registry = DummyRegistry()
    validator = ValidatorWrapper(registry)

    step = Step(
        type="sample_transfer",
        params={
            "labware_source": "missing_plate",
            "labware_target": "dilution_plate",
            "volumes": 25,
            "DiTi_type": "FCA_DiTi_200uL",
            "liquid_class": "Water_Free",
        },
    )

    result = validator.validate_step(step)
    assert result.valid is False
    assert any(e["type"] == "unknown_labware" for e in result.errors)
