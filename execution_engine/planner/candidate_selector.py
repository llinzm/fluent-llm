from typing import List, Any


def _val(obj: Any, key: str, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class CandidateSelector:
    def __init__(self, registry, enable_liquid_inference: bool = True):
        self.registry = registry
        self.enable_liquid_inference = enable_liquid_inference

    def select(self, step) -> List[object]:
        if self.enable_liquid_inference:
            self._infer_liquid_class(step)

        valid = []
        methods = self.registry.methods.values() if isinstance(self.registry.methods, dict) else self.registry.methods

        for method in methods:
            supports = _val(method, "supports", [])
            if step.type not in supports:
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

            # Methods in the current registry expose `requires`, not `device`.
            # Keep behavior permissive here and let scoring/planning resolve preference.
            max_vol = _val(tip, "max_volume") or _val(tip, "max_volume_uL")
            if volume and max_vol and volume > max_vol:
                return False

        liquid_class = step.params.get("liquid_class")
        if liquid_class and tip_type:
            lc = self.registry.get_liquid_class(liquid_class)
            compatible = _val(lc, "compatible_tips", []) or _val(lc, "compatible_tip_types", [])
            if not lc or tip_type not in compatible:
                return False

        return True

    def _infer_liquid_class(self, step) -> None:
        if step.params.get("liquid_class"):
            return

        tip_type = step.params.get("tip_type")
        if not tip_type:
            return

        candidates = []
        liquid_classes = self.registry.liquid_classes.items() if isinstance(self.registry.liquid_classes, dict) else []

        for name, lc in liquid_classes:
            compatible = _val(lc, "compatible_tips", []) or _val(lc, "compatible_tip_types", [])
            if tip_type in compatible:
                candidates.append((name, lc))

        if not candidates:
            return

        def _meta_rank(obj):
            meta = _val(obj, "meta")
            documented = _val(meta, "documented", False)
            return 0 if documented else 1

        candidates.sort(key=lambda x: _meta_rank(x[1]))
        step.params["liquid_class"] = candidates[0][0]
