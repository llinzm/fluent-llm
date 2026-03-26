from typing import Any


def _val(obj: Any, key: str, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class ScoringEngine:
    def __init__(self, registry):
        self.registry = registry
        self.weights = {
            "coverage": 2.0,
            "tip": 2.0,
            "volume": 2.0,
            "liquid": 1.5,
            "efficiency": 1.0,
            "risk": 2.0,
        }

    def score(self, step, method):
        coverage = 1.0 if step.type in (_val(method, "supports", []) or []) else 0.0

        tip_type = step.params.get("tip_type")
        tip_score = 1.0 if tip_type else 0.5

        volume = step.params.get("volume_uL", 0)
        volume_score = 1.0 if volume else 0.5

        liquid_score = 1.0 if step.params.get("liquid_class") else 0.5

        # Current Method model has no explicit `type`, so preserve prior default behavior.
        efficiency = 1.0 if _val(method, "type") == "native" else 0.7
        risk = 0.0

        if tip_type and volume:
            tip = self.registry.get_tip(tip_type)
            max_vol = _val(tip, "max_volume") or _val(tip, "max_volume_uL")
            if max_vol and volume > max_vol:
                risk += 1.0

        score = (
            self.weights["coverage"] * coverage +
            self.weights["tip"] * tip_score +
            self.weights["volume"] * volume_score +
            self.weights["liquid"] * liquid_score +
            self.weights["efficiency"] * efficiency -
            self.weights["risk"] * risk
        )

        return {
            "score": score,
            "reasoning": {
                "coverage": coverage,
                "tip": tip_score,
                "volume": volume_score,
                "liquid": liquid_score,
                "efficiency": efficiency,
                "risk": risk,
            },
        }
