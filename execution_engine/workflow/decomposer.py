from typing import List
from execution_engine.models.workflow import Step, Workflow

class WorkflowDecomposer:
    def decompose(self, assay) -> Workflow:
        steps: List[Step] = []
        for step in assay.steps:
            if step.type == "serial_dilution":
                steps.extend(self._decompose_serial_dilution(step))
            elif step.type == "add_trbc":
                steps.extend(self._decompose_trbc(step))
            else:
                steps.append(step)
        return Workflow(steps=steps)

    def _decompose_serial_dilution(self, step):
        return [
            Step(type="fill_plate", params=step.params),
            Step(type="distribute_antisera", params=step.params),
            Step(type="serial_dilution_core", params=step.params),
            Step(type="add_antigen", params=step.params),
        ]

    def _decompose_trbc(self, step):
        return [
            Step(type="mix_trbc", params=step.params),
            Step(type="distribute_trbc", params=step.params),
        ]
