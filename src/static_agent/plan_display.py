import json
import re
from typing import List, Dict, Any, Set

def _extract_task_references(args: Any) -> Set[str]:
    """Extract all $task_xxx references from args recursively."""
    refs = set()
    if isinstance(args, str):
        for match in re.findall(r'\$task_[a-zA-Z0-9_]+', args):
            refs.add(match)
    elif isinstance(args, dict):
        for v in args.values():
            refs.update(_extract_task_references(v))
    elif isinstance(args, list):
        for item in args:
            refs.update(_extract_task_references(item))
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
    tools_map: Dict[str, Dict[str, Any]] = {}
    for t in tools_metadata:
        name = t.get("name", "")
        tools_map[name] = t

    total = len(plan.tasks)
    lines: List[str] = []

    # Header
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║                📋 STATIC EXECUTION PLAN                      ║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    if plan.reason:
        reason_text = plan.reason
        max_width = 58
        wrapped = [reason_text[i:i + max_width] for i in range(0, len(reason_text), max_width)]
        for line in wrapped:
            lines.append(f"║ {line:<60} ║")
    fallback_label = "ON" if enable_llm_fallback else "OFF"
    lines.append(f"║ Total Tasks: {total} │ Engine: {binding_type.upper():<10} │ Fallback: {fallback_label:<5}  ║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")
    lines.append("")

    for idx, task in enumerate(plan.tasks):
        tool_meta = tools_map.get(task.tool_name, {})
        output_schema = tool_meta.get("outputSchema", tool_meta.get("output_schema", {}))

        task_refs = _extract_task_references(task.args)

        # Step header
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append(f"│ Task {idx + 1}/{total}: {task.tool_name:<49} │")
        if task.reason:
            reason = task.reason[:57] + "..." if len(task.reason) > 57 else task.reason
            lines.append(f"│ Reason: {reason:<52} │")

        # INPUT section
        lines.append("├──────────── INPUT ──────────────────────────────────────────┤")
        input_str = _format_json_indented(task.args, indent=4)
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
        if task_refs:
            deps = ", ".join(sorted(task_refs))
            lines.append(f"│    Depends on: {deps:<45}│")
        else:
            lines.append(f"│    Source: User Input (no dependencies){'':<21}│")

        if task.directive:
            directive = task.directive[:55] + "..." if len(task.directive) > 55 else task.directive
            lines.append(f"│    Directive: {directive:<46}│")

        lines.append("└─────────────────────────────────────────────────────────────┘")

        # Arrow connector between steps
        if idx < total - 1:
            lines.append("          │")
            lines.append("          ▼")

    return "\n".join(lines)
