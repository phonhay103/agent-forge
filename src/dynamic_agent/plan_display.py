import json
from typing import List, Dict, Any


def _format_json_indented(data: Any, indent: int = 4) -> str:
    """Format data as indented JSON string with prefix padding."""
    prefix = " " * indent
    lines = json.dumps(data, indent=2, ensure_ascii=False).split("\n")
    return "\n".join(f"{prefix}{line}" for line in lines)


def format_plan_display(plan: Any, tools_metadata: List[Dict[str, Any]]) -> str:
    """Format a Dynamic Plan for terminal display."""
    total = len(plan.tasks)
    lines: List[str] = []

    lines.append("\u2554" + "\u2550" * 62 + "\u2557")
    lines.append("\u2551" + "            \U0001f4cb DYNAMIC EXECUTION PLAN                       " + "\u2551")
    lines.append("\u2560" + "\u2550" * 62 + "\u2563")
    if plan.reason:
        reason_text = plan.reason
        max_width = 58
        wrapped = [reason_text[i:i + max_width] for i in range(0, len(reason_text), max_width)]
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
        lines.append(f"\u2502    {task.input_description[:57]}")

        lines.append("\u251c" + "\u2500" * 12 + " OUTPUT DESCRIPTION " + "\u2500" * 29 + "\u2524")
        lines.append(f"\u2502    {task.output_description[:57]}")

        lines.append("\u251c" + "\u2500" * 12 + " DEPENDENCIES " + "\u2500" * 35 + "\u2524")
        if task.depends_on:
            deps = ", ".join(task.depends_on)
            lines.append(f"\u2502    Depends on: {deps}")
        else:
            lines.append(f"\u2502    Source: User Input (no dependencies)")

        lines.append("\u2514" + "\u2500" * 61 + "\u2518")
        if idx < total - 1:
            lines.append("          \u2502")
            lines.append("          \u25bc")

    return "\n".join(lines)
