class VariableMapper:
    def map(self, step, method=None):
        t = step.type
        p = step.params

        tip = p.get("tip_type") or p.get("DiTi_type") or p.get("diti_type")

        if t in ["reagent_distribution", "sample_transfer"]:
            return {
                "volumes": p.get("volumes"),
                "tip_type": tip,
                "liquid_class": p.get("liquid_class"),
                "labware_source": p.get("labware_source"),
                "labware_target": p.get("labware_target"),
                "selected_wells_source": p.get("selected_wells_source"),
                "selected_wells_target": p.get("selected_wells_target"),
            }

        elif t in ["aspirate_volume", "dispense_volume", "mix_volume"]:
            return {
                "volumes": p.get("volumes"),
                "labware": p.get("labware"),
                "liquid_class": p.get("liquid_class"),
                "well_offsets": p.get("well_offsets") or p.get("well_offset"),
                "cycles": p.get("cycles"),
            }

        elif t == "transfer_labware":
            return {
                "labware_name": p.get("labware_name"),
                "target_location": p.get("target_location"),
                "target_position": p.get("target_position"),
            }

        elif t == "get_tips":
            return {"tip_type": tip}

        elif t == "drop_tips_to_location":
            return {"labware": p.get("labware")}

        return {k:v for k,v in p.items() if v is not None}
