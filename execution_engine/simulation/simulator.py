
class Simulator:
    def simulate(self, workflow):
        for step in workflow.steps:
            if not hasattr(step, "type"):
                return {"success": False}
        return {"success": True}
