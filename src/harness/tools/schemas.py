"""Tool parameter schemas."""


def parameters_to_json_schema(parameters: dict) -> dict:
    """Convert simple parameter dict to JSON Schema format."""
    properties = {}
    required = []
    for name, spec in parameters.items():
        prop = {"type": spec.get("type", "string")}
        if "description" in spec:
            prop["description"] = spec["description"]
        if "enum" in spec:
            prop["enum"] = spec["enum"]
        properties[name] = prop
        if spec.get("required", False):
            required.append(name)
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }
