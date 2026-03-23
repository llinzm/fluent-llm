
from .candidate_selector import CandidateSelector
from .scoring import ScoringEngine
from .variable_mapper import VariableMapper

class Planner:
    def __init__(self, registry, enable_liquid_inference=True):
        self.selector = CandidateSelector(registry, enable_liquid_inference)
        self.scorer = ScoringEngine(registry)
        self.mapper = VariableMapper()

    def plan(self, step):
        candidates = self.selector.select(step)
        if not candidates:
            raise Exception("No valid candidates found")

        best = None
        best_score = -1

        for method in candidates:
            result = self.scorer.score(step, method)
            if result["score"] > best_score:
                best_score = result["score"]
                best = {
                    "method_name": method["name"],
                    "variables": self.mapper.map(step, method),
                    "score": result["score"],
                    "reasoning": result["reasoning"]
                }

        return best
