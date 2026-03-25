# LLM Module

## Purpose

This module converts natural-language **IFUs (Instructions for Use)** into a structured assay representation (**TDF / JSON**) that can be consumed by the execution engine.

---

## 🚀 What this version supports

* ✅ Real OpenAI integration
* ✅ Structured JSON enforcement (schema-based)
* ✅ Automatic retry on invalid JSON
* ✅ IFU ingestion (string → structured workflow)

---

## 🧩 Components

### 1. `PromptBuilder`

Builds a structured prompt from:

* IFU text
* optional capability hints (e.g. tips, devices)
* optional additional context

---

### 2. `LLMClient`

Handles:

* LLM API calls (OpenAI)
* JSON parsing
* schema validation
* retry loop on malformed output

---

## 🔐 Setup

Set your API key:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

(Windows PowerShell)

```powershell
setx OPENAI_API_KEY "your_api_key_here"
```

---

## 🧪 Full Example — IFU → TDF

### Input IFU

```text
Distribute 50 µL of DPBS buffer into a 96-well plate.
Then incubate for 10 minutes.
```

---

### Python Example

```python
from execution_engine.llm import LLMClient

# 1. Initialize client
client = LLMClient(
    provider="openai",
    model="gpt-4o-mini",
    max_retries=3
)

# 2. Define IFU (this is your entry point)
ifu_text = """
Distribute 50 µL of DPBS buffer into a 96-well plate.
Then incubate for 10 minutes.
"""

# 3. Optional: provide hints from capability registry
capability_hints = {
    "tips": ["FCA_DiTi_200uL", "FCA_DiTi_1000uL"],
    "labware": ["plate_96", "reservoir_12"],
    "devices": ["FCA", "incubator"]
}

# 4. Generate structured assay (TDF)
tdf = client.generate_tdf(
    ifu_text=ifu_text,
    capability_hints=capability_hints
)

# 5. Inspect result
print(tdf)
```

---

### Example Output (TDF)

```json
{
  "steps": [
    {
      "type": "reagent_distribution",
      "params": {
        "volume_uL": 50,
        "liquid": "DPBS",
        "target": "plate_96"
      }
    },
    {
      "type": "incubate",
      "params": {
        "time_s": 600
      }
    }
  ],
  "assumptions": [
    "DPBS is treated as aqueous buffer"
  ],
  "open_questions": []
}
```

---

## 🔁 Retry Behavior (Important)

If the model returns:

* ❌ invalid JSON
* ❌ missing `"steps"`
* ❌ malformed structure

The client will automatically:

1. Append corrective feedback to the prompt
2. Retry the request
3. Fail only after `max_retries`

---

## 🧠 Prompt Strategy

The system prompt enforces:

* structured output only
* no hallucination of missing parameters
* explicit decomposition of workflow steps
* separation of:

  * steps
  * assumptions
  * open questions

---

## ⚙️ Advanced Usage

### Add additional context

```python
tdf = client.generate_tdf(
    ifu_text=ifu_text,
    additional_context="Use low-retention tips for DNA samples"
)
```

---

### Disable hints (minimal mode)

```python
tdf = client.generate_tdf(ifu_text)
```

---

## 🧠 Design Principles

* **Deterministic structure** → schema-enforced JSON
* **Resilient** → retry loop
* **Composable** → plugs into workflow + validation
* **Extensible** → supports future Claude / multi-model

---

## 🔗 Where this fits in the system

```text
IFU (text)
↓
LLM Module (this)
↓
TDF (JSON)
↓
Workflow → Validation → Planner → Runtime
```

---

## 📌 Summary

This module is the **entry point of intelligence** in your system.

It turns:

```text
Human-readable assay → machine-executable workflow
```

And ensures the output is:

* valid
* structured
* usable downstream
