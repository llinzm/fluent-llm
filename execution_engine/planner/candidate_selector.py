
from typing import List

class CandidateSelector:
    def __init__(self, registry, enable_liquid_inference: bool = True):
        self.registry = registry
        self.enable_liquid_inference = enable_liquid_inference

    def select(self, step) -> List[dict]:
        if self.enable_liquid_inference:
            self._infer_liquid_class(step)

        valid = []
        for method in self.registry.methods:
            if step.type not in method.get("supports", []):
                continue
            if not self._validate_hard_constraints(step, method):
                continue
            valid.append(method)
        return valid

    def _validate_hard_constraints(self, step, method) -> bool:
        tip_type = step.params.get("tip_type")
        volume = step.params.get("volume_uL")

        if tip_type:
            tip = self.registry.get_tip(tip_type)
            if not tip:
                return False
            if method.get("device") not in tip.get("compatible_devices", []):
                return False
            if volume and volume > tip.get("max_volume"):
                return False

        liquid_class = step.params.get("liquid_class")
        if liquid_class and tip_type:
            lc = self.registry.get_liquid_class(liquid_class)
            if not lc or tip_type not in lc.get("compatible_tips", []):
                return False

        return True

    def _infer_liquid_class(self, step):
        if step.params.get("liquid_class"):
            return
        tip_type = step.params.get("tip_type")
        if not tip_type:
            return

        candidates = []
        for name, lc in self.registry.liquid_classes.items():
            if tip_type in lc.get("compatible_tips", []):
                candidates.append((name, lc))

        if not candidates:
            return

        candidates.sort(key=lambda x: 0 if x[1].get("meta") == "documented" else 1)
        step.params["liquid_class"] = candidates[0][0]
