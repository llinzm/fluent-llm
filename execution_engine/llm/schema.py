TDF_JSON_SCHEMA = {
    "name": "structured_assay_tdf",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "assay_id": {"type": ["string", "null"]},
            "intent": {"type": ["string", "null"]},
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "type": {"type": "string"},
                        "params": {
                            "type": "object",
                            "additionalProperties": True
                        }
                    },
                    "required": ["type", "params"]
                }
            },
            "open_questions": {
                "type": "array",
                "items": {"type": "string"}
            },
            "assumptions": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["steps"]
    }
}
