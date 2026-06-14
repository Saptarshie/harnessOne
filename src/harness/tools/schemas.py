"""Tool parameter schemas."""


def parameters_to_json_schema(parameters: dict) -> dict:
    """Convert parameter dict to JSON Schema format.

    Handles both:
    - Simple format: {"param": {"type": "string", "description": "..."}}
    - JSON Schema format: {"type": "object", "properties": {...}, "required": [...]}
    """
    # Already JSON Schema format (from MCP servers)
    if parameters.get("type") == "object":
        return {
            "type": "object",
            "properties": parameters.get("properties", {}),
            "required": parameters.get("required", []),
        }

    # Simple format (built-in tools)
    properties = {}
    required = []
    for name, spec in parameters.items():
        if isinstance(spec, dict):
            prop = {"type": spec.get("type", "string")}
            if "description" in spec:
                prop["description"] = spec["description"]
            if "enum" in spec:
                prop["enum"] = spec["enum"]
            properties[name] = prop
            if spec.get("required", False):
                required.append(name)
        else:
            # Fallback for unexpected format
            properties[name] = {"type": "string"}

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }
