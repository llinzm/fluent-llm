
class VariableMapper:
     def map(self, step, method):
        raw = {
            "volume_uL": step.params.get("volume_uL"),
            "tip_type": step.params.get("tip_type"),
            "liquid_class": step.params.get("liquid_class"),
            "source": step.params.get("source"),
            "target": step.params.get("target"),
        }

        # ✅ REMOVE None values (critical fix)
        return {k: v for k, v in raw.items() if v is not None}
