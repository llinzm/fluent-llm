from execution_engine.models.workflow import Workflow, Step


def simple_distribution():
    return Workflow(
        steps=[
            Step(
                type="reagent_distribution",
                params={
                    "volume_uL": 50,
                    "liquid": "DPBS",
                    "liquid_class": "Water_Free",
                    "tip_type": "FCA_DiTi_200uL",
                    "source": "Trough_25mL:A1",
                    "target": "Plate_96:A1"
                }
            )
        ]
    )


def distribution_with_incubation():
    return Workflow(
        steps=[
            Step(
                type="reagent_distribution",
                params={
                    "volume_uL": 30,
                    "liquid": "DPBS",
                    "liquid_class": "Water_Free",
                    "tip_type": "FCA_DiTi_50uL",
                    "source": "Trough_25mL:A1",
                    "target": "Plate_96:B1"
                }
            ),
            Step(
                type="incubate",
                params={
                    "time_s": 300,
                    "location": "Heated_Incubator",
                    "labware": "Plate_96"
                }
            )
        ]
    )


def distribution_mix_incubate():
    return Workflow(
        steps=[
            Step(
                type="reagent_distribution",
                params={
                    "volume_uL": 20,
                    "liquid": "DPBS",
                    "liquid_class": "Water_Free",
                    "tip_type": "FCA_DiTi_50uL",
                    "source": "Trough_25mL:A1",
                    "target": "Plate_96:C1"
                }
            ),
            Step(
                type="mix",
                params={
                    "volume_uL": 15,
                    "cycles": 3,
                    "target": "Plate_96:C1",
                    "liquid_class": "Water_Free",
                    "tip_type": "FCA_DiTi_50uL" 
                }
            ),
            Step(
                type="incubate",
                params={
                    "time_s": 600,
                    "location": "Heated_Incubator",
                    "labware": "Plate_96"
                }
            )
        ]
    )