import json
import re
from typing import Any


def _extract_task_references(args: Any) -> set[str]:
    """Extract all $task_xxx references from args recursively."""
    refs = set()
    if isinstance(args, str):
        for match in re.findall(r"\$task_[a-zA-Z0-9_]+", args):
            refs.add(match)
    elif isinstance(args, dict):
        for v in args.values():
            refs.update(_extract_task_references(v))
    elif isinstance(args, list):
        for item in args:
            refs.update(_extract_task_references(item))
    return refs


def _simplify_schema(schema: dict[str, Any], max_depth: int = 2) -> dict[str, Any]:
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
    tools_metadata: list[dict[str, Any]],
    binding_type: str = "jmespath",
) -> str:
    # Check if this is a dynamic/hybrid plan
    is_dynamic = any(
        getattr(task, "input_description", None) is not None or getattr(task, "args_jmespath", None) is not None
        for task in plan.tasks
    )

    if is_dynamic:
        total = len(plan.tasks)
        lines: list[str] = []

        lines.append("\u2554" + "\u2550" * 62 + "\u2557")
        lines.append("\u2551" + "            \U0001f4cb DYNAMIC EXECUTION PLAN                       " + "\u2551")
        lines.append("\u2560" + "\u2550" * 62 + "\u2563")
        if plan.reason:
            reason_text = plan.reason
            max_width = 58
            wrapped = [reason_text[i : i + max_width] for i in range(0, len(reason_text), max_width)]
            for line in wrapped:
                lines.append(f"\u2551 {line:<60} \u2551")
        lines.append(f"\u2551 Total Tasks: {total} \u2502 Binding: LLM Runtime Schema-Match{'':<10}\u2551")
        lines.append("\u255a" + "\u2550" * 62 + "\u255d")
        lines.append("")

        for idx, task in enumerate(plan.tasks):
            lines.append("\u250c" + "\u2500" * 61 + "\u2510")
            tool_display = task.tool_name[:49] if len(task.tool_name) > 49 else task.tool_name
            lines.append(f"\u2502 Task {idx + 1}/{total} [{task.id}]: {tool_display}")
            if task.reason:
                reason = task.reason[:55] + "..." if len(task.reason) > 55 else task.reason
                lines.append(f"\u2502 Reason: {reason}")

            lines.append("\u251c" + "\u2500" * 12 + " INPUT DESCRIPTION " + "\u2500" * 30 + "\u2524")
            input_desc = task.input_description or ""
            lines.append(f"\u2502    {input_desc[:57]}")

            lines.append("\u251c" + "\u2500" * 12 + " OUTPUT DESCRIPTION " + "\u2500" * 29 + "\u2524")
            output_desc = task.output_description or ""
            lines.append(f"\u2502    {output_desc[:57]}")

            lines.append("\u251c" + "\u2500" * 12 + " DEPENDENCIES " + "\u2500" * 35 + "\u2524")
            if task.depends_on:
                deps = ", ".join(task.depends_on)
                lines.append(f"\u2502    Depends on: {deps}")
            else:
                lines.append("\u2502    Source: User Input (no dependencies)")

            if getattr(task, "args_jmespath", None):
                lines.append(f"\u2502    Planned JMESPath: {task.args_jmespath}")

            lines.append("\u2514" + "\u2500" * 61 + "\u2518")
            if idx < total - 1:
                lines.append("          \u2502")
                lines.append("          \u25bc")

        return "\n".join(lines)

    else:
        tools_map: dict[str, dict[str, Any]] = {}
        for t in tools_metadata:
            name = t.get("name", "")
            tools_map[name] = t

        total = len(plan.tasks)
        lines: list[str] = []

        # Header
        lines.append("╔══════════════════════════════════════════════════════════════╗")
        lines.append("║                📋 STATIC EXECUTION PLAN                      ║")
        lines.append("╠══════════════════════════════════════════════════════════════╣")
        if plan.reason:
            reason_text = plan.reason
            max_width = 58
            wrapped = [reason_text[i : i + max_width] for i in range(0, len(reason_text), max_width)]
            for line in wrapped:
                lines.append(f"║ {line:<60} ║")
        lines.append(f"║ Total Tasks: {total:<2} │ Engine: {binding_type.upper():<10}{' ' * 24}║")
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

            lines.append("└─────────────────────────────────────────────────────────────┘")

            # Arrow connector between steps
            if idx < total - 1:
                lines.append("          │")
                lines.append("          ▼")

        return "\n".join(lines)
