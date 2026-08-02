import json
import re
from typing import List, Dict, Any, Set


def _extract_step_references(args: Any) -> Set[str]:
    """Extract all $step_N references from args recursively."""
    refs = set()
    if isinstance(args, str):
        for match in re.findall(r'\$step_\d+', args):
            refs.add(match)
    elif isinstance(args, dict):
        for v in args.values():
            refs.update(_extract_step_references(v))
    elif isinstance(args, list):
        for item in args:
            refs.update(_extract_step_references(item))
    return refs


def _simplify_schema(schema: Dict[str, Any], max_depth: int = 2) -> Dict[str, Any]:
    """Simplify a JSON schema into a human-readable summary of key: type."""
    if not schema or not isinstance(schema, dict):
        return {}

    properties = schema.get("properties", {})
    result = {}
    for key, prop in properties.items():
        prop_type = prop.get("type", "any")
        if prop_type == "array":
            items = prop.get("items", {})
            items_type = items.get("type", "object")
            if items_type == "object" and "properties" in items and max_depth > 0:
                nested = _simplify_schema(items, max_depth - 1)
                result[key] = f"List[{{{', '.join(f'{k}: {v}' for k, v in nested.items())}}}]"
            else:
                title = items.get("title", items_type)
                result[key] = f"List[{title}]"
        elif prop_type == "object" and "properties" in prop and max_depth > 0:
            nested = _simplify_schema(prop, max_depth - 1)
            result[key] = f"{{{', '.join(f'{k}: {v}' for k, v in nested.items())}}}"
        else:
            result[key] = prop.get("title", prop_type)
    return result


def _format_json_indented(data: Any, indent: int = 4) -> str:
    """Format data as indented JSON string with prefix padding."""
    prefix = " " * indent
    lines = json.dumps(data, indent=2, ensure_ascii=False).split("\n")
    return "\n".join(f"{prefix}{line}" for line in lines)


def format_plan_display(
    plan: Any,
    tools_metadata: List[Dict[str, Any]],
    binding_type: str = "jmespath",
    enable_llm_fallback: bool = False,
) -> str:
    """
    Format a Plan into a human-readable display string with input/output info per step.

    Args:
        plan: A Plan object with .steps and optional .reason
        tools_metadata: List of tool metadata dicts from MCP server (containing inputSchema/outputSchema)
        binding_type: The active binding engine name
        enable_llm_fallback: Whether LLM fallback is enabled

    Returns:
        Formatted string for terminal display
    """
    tools_map: Dict[str, Dict[str, Any]] = {}
    for t in tools_metadata:
        name = t.get("name", "")
        tools_map[name] = t

    total = len(plan.steps)
    lines: List[str] = []

    # Header
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║                    📋 EXECUTION PLAN                        ║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    if plan.reason:
        reason_text = plan.reason
        max_width = 58
        wrapped = [reason_text[i:i + max_width] for i in range(0, len(reason_text), max_width)]
        for line in wrapped:
            lines.append(f"║ {line:<60} ║")
    fallback_label = "ON" if enable_llm_fallback else "OFF"
    lines.append(f"║ Total Steps: {total} │ Engine: {binding_type.upper():<10} │ Fallback: {fallback_label:<5}  ║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")
    lines.append("")

    for idx, step in enumerate(plan.steps):
        tool_meta = tools_map.get(step.tool_name, {})
        output_schema = tool_meta.get("outputSchema", tool_meta.get("output_schema", {}))

        step_refs = _extract_step_references(step.args)

        # Step header
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append(f"│ Step {idx + 1}/{total}: {step.tool_name:<49} │")
        if step.reason:
            reason = step.reason[:57] + "..." if len(step.reason) > 57 else step.reason
            lines.append(f"│ Reason: {reason:<52} │")

        # INPUT section
        lines.append("├──────────── INPUT ──────────────────────────────────────────┤")
        input_str = _format_json_indented(step.args, indent=4)
        for line in input_str.split("\n"):
            lines.append(f"│ {line:<60}│")

        # OUTPUT SCHEMA section
        if output_schema:
            lines.append("├──────────── OUTPUT SCHEMA ──────────────────────────────────┤")
            simplified = _simplify_schema(output_schema)
            if simplified:
                schema_str = _format_json_indented(simplified, indent=4)
            else:
                schema_str = _format_json_indented(output_schema, indent=4)
            for line in schema_str.split("\n"):
                lines.append(f"│ {line:<60}│")

        # DATA FLOW section
        lines.append("├──────────── DATA FLOW ──────────────────────────────────────┤")
        if step_refs:
            deps = ", ".join(sorted(step_refs))
            lines.append(f"│    Depends on: {deps:<45}│")
        else:
            lines.append(f"│    Source: User Input (no dependencies){'':<21}│")

        if step.directive:
            directive = step.directive[:55] + "..." if len(step.directive) > 55 else step.directive
            lines.append(f"│    Directive: {directive:<46}│")

        lines.append("└─────────────────────────────────────────────────────────────┘")

        # Arrow connector between steps
        if idx < total - 1:
            lines.append("          │")
            lines.append("          ▼")

    return "\n".join(lines)
