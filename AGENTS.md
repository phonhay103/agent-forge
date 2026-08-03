# Agent Guidelines & Design Principles

## 1. Loose Coupling & Separation of Concerns
- **Zero Concrete Library Coupling**: Business logic classes must never import concrete transport layers, prompt rendering engines, or LLM providers.
- **Unified Factory & Interface Delegation**: Wrap external libraries behind centralized factories, registry managers, or Python Protocols.


## 2. Codebase Search & Analysis
- **Prefer AST-based Search for Structural Code Analysis**: When exploring the codebase to understand class hierarchies, decorators, function signatures, or specific syntax patterns, favor `ast_search` over plain text searches like `grep`. This eliminates false positives (such as comments or string literals) and accurately targets structural nodes regardless of code formatting.


## 3. Vertical Slice Architecture (VSA)
- **Feature-Centric Slice Organization**: Packages and components should organize files by feature or capability (e.g. format-specific parsers/composers) rather than horizontal technology layers. Each slice should be fully self-contained.
- **Unified Factory Delegation**: Centralize entry points under unified interfaces or facades (e.g. `PromptComposer`) that dynamically select and delegate to vertical format slices based on format detection or configurations.

