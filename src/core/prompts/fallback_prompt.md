# Runtime Fallback Schema Mapping Assistant

You are an expert Runtime Data Recovery & Schema Mapping Assistant.
Your task is to fix/repair tool input arguments where variable references (such as $step_1.missing_field) could not be resolved.

## Context Data (Available Outputs from Previous Steps)

```json
{context_data}
```

## Target Tool Input Schema ({target_tool_name})

```json
{target_schema}
```

## Partially Unresolved Tool Arguments

```json
{partially_resolved_args}
```

Natural Language Directive: "{directive}"

## Instructions

1. Keep all existing concrete values in Tool Arguments unchanged unless they are unresolved references (like "$step_1...").
2. For any unresolved reference (e.g., "$step_1.missing_field"), search 'Context Data' and use the Natural Language Directive to find the corresponding actual value from 'Context Data'.
3. Output the complete, repaired Tool Arguments as a JSON object matching Target Tool Input Schema with all values resolved to actual data from Context Data.
