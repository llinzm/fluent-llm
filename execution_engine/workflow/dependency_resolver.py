class DependencyResolver:
    def validate(self, workflow):
        seen = set()
        for step in workflow.steps:
            if step.type == "mix" and "fill_plate" not in seen:
                raise Exception("Cannot mix before liquid is added")
            if step.type == "incubate" and "add_antigen" not in seen:
                raise Exception("Cannot incubate before reagents are added")
            seen.add(step.type)
        return True
