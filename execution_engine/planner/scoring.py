
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
        coverage = 1.0 if step.type in method.get("supports", []) else 0.0
        tip_score = 1.0 if step.params.get("tip_type") else 0.5
        volume = step.params.get("volume_uL", 0)
        volume_score = 1.0 if volume else 0.5
        liquid_score = 1.0 if step.params.get("liquid_class") else 0.5
        efficiency = 1.0 if method.get("type") == "native" else 0.7
        risk = 0.0

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
                "risk": risk
            }
        }
