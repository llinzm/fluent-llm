class WorkflowState:
    def __init__(self):
        self.well_volumes = {}
        self.tip_loaded = False

    def update(self, step):
        if step.type in ["fill_plate", "distribute_antisera", "add_antigen"]:
            for well, volume in step.params.get("volumes", {}).items():
                self.well_volumes[well] = self.well_volumes.get(well, 0) + volume

        if step.type == "aspirate":
            self.tip_loaded = True

        if step.type == "dispense":
            self.tip_loaded = False

    def get_volume(self, well):
        return self.well_volumes.get(well, 0)
