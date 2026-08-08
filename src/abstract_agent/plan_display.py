from typing import Any


def format_plan_display(plan: Any, _tools_metadata: list[dict[str, Any]]) -> str:
    """Format an Abstract Plan for terminal display."""
    total = len(plan.tasks)
    lines: list[str] = []

    lines.append("\u2554" + "\u2550" * 62 + "\u2557")
    lines.append("\u2551" + "           \U0001f4cb ABSTRACT EXECUTION PLAN                      " + "\u2551")
    lines.append("\u2560" + "\u2550" * 62 + "\u2563")
    if plan.reason:
        reason_text = plan.reason
        max_width = 58
        wrapped = [reason_text[i : i + max_width] for i in range(0, len(reason_text), max_width)]
        for line in wrapped:
            lines.append(f"\u2551 {line:<60} \u2551")
    lines.append(f"\u2551 Total Tasks: {total} \u2502 Binding: LLM Runtime (Tool + Data){'':<8}\u2551")
    lines.append("\u255a" + "\u2550" * 62 + "\u255d")
    lines.append("")

    for idx, task in enumerate(plan.tasks):
        lines.append("\u250c" + "\u2500" * 61 + "\u2510")
        lines.append(f"\u2502 Task {idx + 1}/{total} [{task.id}]")

        lines.append("\u251c" + "\u2500" * 12 + " INTENT " + "\u2500" * 41 + "\u2524")
        lines.append(f"\u2502    {task.intent[:57]}")

        lines.append("\u251c" + "\u2500" * 12 + " EXPECTED I/O " + "\u2500" * 35 + "\u2524")
        lines.append(f"\u2502    Input:  {(task.expected_input or 'N/A')[:50]}")
        lines.append(f"\u2502    Output: {(task.expected_output or 'N/A')[:50]}")

        lines.append("\u251c" + "\u2500" * 12 + " DEPENDENCIES " + "\u2500" * 35 + "\u2524")
        if task.depends_on:
            deps = ", ".join(task.depends_on)
            lines.append(f"\u2502    Depends on: {deps}")
        else:
            lines.append("\u2502    Source: User Input")

        lines.append("\u2514" + "\u2500" * 61 + "\u2518")
        if idx < total - 1:
            lines.append("          \u2502")
            lines.append("          \u25bc")

    return "\n".join(lines)
