# Create a Word document containing exactly the previous response content (no additions or removals)

Here is a **full worked example** for the path:
```
IFU
↓
LLM
↓
Structured Assay Model (TDF / JSON)
↓
Validation Engine
↓
PyFluent Workflow API
    chooses:
    - method_name = "ReagentDistribution_With_Incubation"
    - variables = {...}
↓
run_method(method_name, variables)
↓
PrepareMethod(method_name)
SetVariableValue(...)
runtime.RunMethod()
↓
FluentControl method executes
```


---

## 1) IFU

Human input:

> Distribute 50 µL buffer to a 96-well plate,
> mix 3 times, 
> incubate 10 minutes.

Problem: this is **not executable** yet. Fluent-style execution still needs explicit choices such as labware identity, liquid class, tips, and device/tool selection. FluentControl worklist loading also expects concrete arm, liquid class, tip handling, and related settings; it also has explicit behaviors for missing labware and dynamic tip handling.

---

## 2) LLM step

The LLM should **not** generate robot commands directly.
Its job is to convert the IFU into a **structured assay request**.

### Example system prompt to the LLM
```python
SYSTEM_PROMPT = """
You are an assay planner.

Convert the user request into JSON only.
Do not generate robot commands.
Do not invent missing physical facts silently.

Rules:
- Output a structured assay request.
- If a value is missing, mark it as null and add it to "open_questions" or "assumptions".
- Use high-level step types only:
  reagent_distribution, mix, incubate
- Do not assign deck positions unless explicitly provided.
- Do not assign a liquid class unless known from assay metadata.
- Output valid JSON only.
"""
```

### Example user prompt
```python
user_ifu = """
Distribute 50 µL buffer to a 96-well plate,
mix 3 times,
incubate 10 minutes.
"""
```

### Example LLM output

```json
{
  "assay_id": "assay_001",
  "intent": "buffer_distribution_with_mix_and_incubation",
  "labware": {
    "source": {
      "role": "buffer_source",
      "labware_id": null,
      "labware_type": "reservoir",
      "well": "A1"
    },
    "destination": {
      "role": "assay_plate",
      "labware_id": null,
      "labware_type": "96_well_plate"
    }
  },
  "liquids": [
    {
      "name": "buffer",
      "liquid_class": null
    }
  ],
  "steps": [
    {
      "type": "reagent_distribution",
      "source_role": "buffer_source",
      "destination_role": "assay_plate",
      "target_wells": "A1:H12",
      "volume_uL": 50
    },
    {
      "type": "mix",
      "target_role": "assay_plate",
      "cycles": 3,
      "volume_uL": 40
    },
    {
      "type": "incubate",
      "target_role": "assay_plate",
      "duration_s": 600,
      "temperature_C": null
    }
  ],
  "constraints": {
    "tip_type": null,
    "channels": null,
    "deck_location_required": true
  },
  "open_questions": [
    "What is the source labware ID for the buffer?",
    "What is the destination plate ID?",
    "Which liquid class should be used for buffer?",
    "Which tip type should be used?",
    "Is incubation at room temperature or controlled temperature?"
  ],
  "assumptions": []
}
```
This is already much safer than letting the LLM emit direct commands.

---

## 3) Structured Assay Model (TDF / JSON)

Now convert that JSON into a typed internal model.

### Example Python data model
```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class LabwareRef:
    role: str
    labware_id: Optional[str]
    labware_type: str
    well: Optional[str] = None

@dataclass
class LiquidRef:
    name: str
    liquid_class: Optional[str]

@dataclass
class Step:
    type: str

@dataclass
class ReagentDistributionStep(Step):
    source_role: str
    destination_role: str
    target_wells: str
    volume_uL: float

@dataclass
class MixStep(Step):
    target_role: str
    cycles: int
    volume_uL: float

@dataclass
class IncubateStep(Step):
    target_role: str
    duration_s: int
    temperature_C: Optional[float]

@dataclass
class AssayModel:
    assay_id: str
    source: LabwareRef
    destination: LabwareRef
    liquids: List[LiquidRef]
    steps: List[Step]
    tip_type: Optional[str]
    channels: Optional[int]
    open_questions: List[str] = field(default_factory=list)

```

### Example parser

```python

def parse_assay_json(data: dict) -> AssayModel:
    source = LabwareRef(**data["labware"]["source"])
    destination = LabwareRef(**data["labware"]["destination"])
    liquids = [LiquidRef(**x) for x in data["liquids"]]

    parsed_steps = []
    for s in data["steps"]:
        if s["type"] == "reagent_distribution":
            parsed_steps.append(ReagentDistributionStep(**s))
        elif s["type"] == "mix":
            parsed_steps.append(MixStep(**s))
        elif s["type"] == "incubate":
            parsed_steps.append(IncubateStep(**s))
        else:
            raise ValueError(f"Unsupported step type: {s['type']}")

    return AssayModel(
        assay_id=data["assay_id"],
        source=source,
        destination=destination,
        liquids=liquids,
        steps=parsed_steps,
        tip_type=data["constraints"]["tip_type"],
        channels=data["constraints"]["channels"],
        open_questions=data.get("open_questions", [])
    )
```
---

## 4) Validation Engine

This is the **critical safety boundary**.

It resolves or rejects missing assumptions before anything reaches PyFluent.

### Example runtime context
```python

deck_state = {
    "labware": {
        "RESERVOIR_BUFFER_01": {"type": "reservoir", "position": "Deck_1"},
        "PLATE_ASSAY_01": {"type": "96_well_plate", "position": "Deck_5"}
    },
    "devices": {
        "fca": {"available": True, "max_channels": 8},
        "shaker": {"available": True},
        "incubator": {"available": True}
    },
    "tips": {
        "FCA_DiTi_200uL_Filtered": {"available": True, "max_volume_uL": 200}
    },
    "liquid_classes": {
        "Buffer_Aqueous": {"compatible_tip_types": ["FCA_DiTi_200uL_Filtered"]}
    }
}
```

### Example validation logic

```python
class ValidationError(Exception):
    pass

def validate_assay(model: AssayModel, deck_state: dict) -> AssayModel:
    if model.source.labware_id is None:
        candidates = [
            k for k, v in deck_state["labware"].items()
            if v["type"] == model.source.labware_type
        ]
        if len(candidates) == 1:
            model.source.labware_id = candidates[0]
        else:
            raise ValidationError("Source labware_id is ambiguous or missing.")

    if model.destination.labware_id is None:
        candidates = [
            k for k, v in deck_state["labware"].items()
            if v["type"] == model.destination.labware_type
        ]
        if len(candidates) == 1:
            model.destination.labware_id = candidates[0]
        else:
            raise ValidationError("Destination labware_id is ambiguous or missing.")

    if model.liquids[0].liquid_class is None:
        model.liquids[0].liquid_class = "Buffer_Aqueous"

    if model.tip_type is None:
        model.tip_type = "FCA_DiTi_200uL_Filtered"

    if model.channels is None:
        model.channels = 8

    lc = model.liquids[0].liquid_class
    tip = model.tip_type
    compatible = deck_state["liquid_classes"][lc]["compatible_tip_types"]
    if tip not in compatible:
        raise ValidationError(f"Tip {tip} is incompatible with liquid class {lc}")

    tip_max = deck_state["tips"][tip]["max_volume_uL"]
    for step in model.steps:
        if hasattr(step, "volume_uL") and step.volume_uL > tip_max:
            raise ValidationError(f"Volume {step.volume_uL} exceeds tip max {tip_max}")

    for step in model.steps:
        if step.type == "reagent_distribution" and not deck_state["devices"]["fca"]["available"]:
            raise ValidationError("FCA not available")
        if step.type == "incubate" and not deck_state["devices"]["incubator"]["available"]:
            raise ValidationError("Incubator not available")

    return model

```

### Validated result

After validation, the model becomes:

```json

{
  "assay_id": "assay_001",
  "source.labware_id": "RESERVOIR_BUFFER_01",
  "destination.labware_id": "PLATE_ASSAY_01",
  "liquid_class": "Buffer_Aqueous",
  "tip_type": "FCA_DiTi_200uL_Filtered",
  "channels": 8
}
```

This is the point where the request becomes executable.

---

## 5) PyFluent Workflow API

Now the workflow layer composes validated steps into `PyFluent` calls. The following example is for illustration only purpose. USe the appropriate `PyFluent` syntax instead.

### Example workflow API

```python

class PyFluentWorkflowAPI:
    def __init__(self, runtime):
        self.runtime = runtime

    def reagent_distribution(
        self,
        source_labware_id: str,
        source_well: str,
        dest_labware_id: str,
        target_wells: str,
        volume_uL: float,
        liquid_class: str,
        tip_type: str,
        channels: int,
    ):
        print(f"[PyFluent] distribute {volume_uL}uL from "
              f"{source_labware_id}:{source_well} to {dest_labware_id} {target_wells}")

    def mix(
        self,
        target_labware_id: str,
        cycles: int,
        volume_uL: float,
        liquid_class: str,
        tip_type: str,
    ):
        print(f"[PyFluent] mix {target_labware_id} cycles={cycles} volume={volume_uL}")

    def incubate(
        self,
        target_labware_id: str,
        duration_s: int,
        temperature_C: float | None = None
    ):
        print(f"[PyFluent] incubate {target_labware_id} for {duration_s}s temp={temperature_C}")
```

### Example executor

```python

def execute_assay(model: AssayModel, api: PyFluentWorkflowAPI):
    liquid_class = model.liquids[0].liquid_class
    tip_type = model.tip_type

    for step in model.steps:
        if isinstance(step, ReagentDistributionStep):
            api.reagent_distribution(
                source_labware_id=model.source.labware_id,
                source_well=model.source.well or "A1",
                dest_labware_id=model.destination.labware_id,
                target_wells=step.target_wells,
                volume_uL=step.volume_uL,
                liquid_class=liquid_class,
                tip_type=tip_type,
                channels=model.channels,
            )

        elif isinstance(step, MixStep):
            api.mix(
                target_labware_id=model.destination.labware_id,
                cycles=step.cycles,
                volume_uL=step.volume_uL,
                liquid_class=liquid_class,
                tip_type=tip_type,
            )

        elif isinstance(step, IncubateStep):
            api.incubate(
                target_labware_id=model.destination.labware_id,
                duration_s=step.duration_s,
                temperature_C=step.temperature_C,
            )
```

### End-to-end usage

```python
raw_llm_json = {
    "assay_id": "assay_001",
    "labware": {
        "source": {"role": "buffer_source", "labware_id": None, "labware_type": "reservoir", "well": "A1"},
        "destination": {"role": "assay_plate", "labware_id": None, "labware_type": "96_well_plate"}
    },
    "liquids": [{"name": "buffer", "liquid_class": None}],
    "steps": [
        {"type": "reagent_distribution", "source_role": "buffer_source", "destination_role": "assay_plate", "target_wells": "A1:H12", "volume_uL": 50},
        {"type": "mix", "target_role": "assay_plate", "cycles": 3, "volume_uL": 40},
        {"type": "incubate", "target_role": "assay_plate", "duration_s": 600, "temperature_C": None}
    ],
    "constraints": {"tip_type": None, "channels": None},
    "open_questions": []
}

model = parse_assay_json(raw_llm_json)
validated_model = validate_assay(model, deck_state)

api = PyFluentWorkflowAPI(runtime=None)
execute_assay(validated_model, api)
```

Output:
```plain text
[PyFluent] distribute 50uL from RESERVOIR_BUFFER_01:A1 to PLATE_ASSAY_01 A1:H12
[PyFluent] mix PLATE_ASSAY_01 cycles=3 volume=40
[PyFluent] incubate PLATE_ASSAY_01 for 600s temp=None
```

---

## 6) Why this is safer

The reason this architecture is safer is that Fluent-style execution needs explicit concrete parameters. Worklist loading in FluentControl requires arm, liquid class, tips, wash/waste behavior, and defines explicit handling for missing labware; dynamic tip handling is also explicitly supported for commands such as Load Worklist, Sample Transfer, and Reagent Distribution.

So the LLM should produce structured intent, while the validator resolves or rejects execution-critical details.

---

## 7) Practical mental model

Use the layers like this:
```plain text
IFU = what the scientist wants
LLM = converts intent to structured assay request
Assay Model = machine-readable plan
Validation Engine = resolves / checks physical reality
PyFluent Workflow = executes only validated steps
```

That is the sweet spot:
- LLM handles semantics
- deterministic code handles safety
- PyFluent handles orchestration

## 8) run_method()
In the current PyFluent implementation, robot execution is not triggered directly by the workflow API.
Instead, the workflow layer selects a FluentControl method and passes variables to it through the MethodManager.
The method manager then invokes FluentControl through the runtime API.

```
PyFluent Workflow API
↓
MethodManager.run_method()
↓
runtime.RunMethod()
```

This step forms the execution boundary between Python orchestration and FluentControl execution.

## Example call from Workflow API
After the validated assay model is converted to a workflow, the executor prepares the method call.

```python
method_name = "ReagentDistribution_With_Incubation"

variables = {
    "SOURCE_LABWARE": "RESERVOIR_BUFFER_01",
    "SOURCE_WELL": "A1",
    "DEST_LABWARE": "PLATE_ASSAY_01",
    "DEST_WELLS": "A1:H12",
    "VOLUME_UL": "50",
    "LIQUID_CLASS": "Buffer_Aqueous",
    "MIX_CYCLES": "3",
    "INCUBATION_SECONDS": "600"
}

method_manager.run_method(
    method_name=method_name,
    variables=variables
)
```

## Simplified behavior of `run_method()`
The current repository implementation behaves conceptually like this:

```python
def run_method(self, method_name=None, variables=None):

    if not self.runtime:
        raise RuntimeError("Runtime not connected")

    if method_name:
        self.prepare_method(method_name)

    if variables:
        for name, value in variables.items():
            self.set_variable(name, value)

    self.runtime.RunMethod()

    return True
```

Execution sequence:

> 1. prepare_method(method_name)
> 2. set_variable(name, value)
> 3. runtime.RunMethod()

So **Python does not execute robot commands directly.**
It **configures and launches a FluentControl method.**

## 9) XML Method

The FluentControl method is the deterministic automation logic executed by the robot.

These methods are authored in FluentControl and stored as XML method files.

They typically include:

* worktable / deck configuration
* device configuration
* liquid handling commands
* tip handling logic
* error handling rules

The Python layer only supplies variables.

## Example method concept
Example FluentControl method:

`ReagentDistribution_With_Incubation`

Internally the XML method might contain steps like:

```
1  Load Worktable
2  Pick up tips
3  Aspirate SOURCE_LABWARE:SOURCE_WELL
4  Dispense to DEST_WELLS
5  Mix MIX_CYCLES times
6  Move plate to incubator
7  Wait INCUBATION_SECONDS
8  Return plate
9  Dispose tips
```

The XML file defines the full deterministic robot sequence.

## Simplified XML illustration
Example conceptual XML structure:

```xml
<Method name="ReagentDistribution_With_Incubation">

    <Variables>
        <Variable name="SOURCE_LABWARE"/>
        <Variable name="SOURCE_WELL"/>
        <Variable name="DEST_LABWARE"/>
        <Variable name="DEST_WELLS"/>
        <Variable name="VOLUME_UL"/>
        <Variable name="LIQUID_CLASS"/>
        <Variable name="MIX_CYCLES"/>
        <Variable name="INCUBATION_SECONDS"/>
    </Variables>

    <Commands>

        <PickTips/>

        <Aspirate
            labware="$SOURCE_LABWARE"
            well="$SOURCE_WELL"
            volume="$VOLUME_UL"
            liquidClass="$LIQUID_CLASS"
        />

        <Dispense
            labware="$DEST_LABWARE"
            wells="$DEST_WELLS"
        />

        <Mix
            cycles="$MIX_CYCLES"
        />

        <Incubate
            duration="$INCUBATION_SECONDS"
        />

        <DropTips/>

    </Commands>

</Method>
```

## 10) Final Execution Flow
The full architecture now becomes:
```
IFU
↓
LLM
↓
Structured Assay Model (JSON / TDF)
↓
Validation Engine
↓
PyFluent Workflow API
↓
MethodManager.run_method()
↓
FluentControl XML Method
↓
runtime.RunMethod()
↓
Robot Execution
```

## 11) Practical Design Principle

This architecture deliberately separates responsibilities:

| Layer             | Responsibility                    |
| ----------------- | --------------------------------- |
| LLM               | Extract scientific intent         |
| Assay Model       | Represent structured workflow     |
| Validation Engine | Ensure physical feasibility       |
| PyFluent          | Orchestrate execution             |
| FluentControl XML | Execute deterministic robot logic |

This separation ensures:

* LLM never controls hardware directly
* all robot actions remain deterministic
* `FluentControl` remains the authoritative execution layer


## TODO:

* Make planner smarter (true optimization engine)
* Add execution feedback loop
* Turn this into a productized SDK
* Design UI / API layer on top
